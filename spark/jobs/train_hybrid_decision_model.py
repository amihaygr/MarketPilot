"""Train and register a calibrated Phase 15 model as PREVIEW."""

from __future__ import annotations

import argparse
import io
import json
import os
import statistics
from uuid import uuid4

import boto3
import pymysql
from pymysql.cursors import DictCursor

from marketpilot.decision_intelligence.modeling import (
    FEATURE_NAMES,
    TrainingRow,
    artifact_manifest,
    feature_values,
    train_walk_forward,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=str(uuid4()))
    parser.add_argument("--model-version", required=True)
    parser.add_argument(
        "--models-bucket", default=os.environ.get("MINIO_MODELS_BUCKET", "marketpilot-models")
    )
    args = parser.parse_args()
    try:
        import joblib
    except ImportError as error:
        raise RuntimeError("joblib is required in the Spark image") from error

    connection = pymysql.connect(
        host=os.environ["MARIADB_HOST"],
        port=int(os.environ.get("MARIADB_PORT", "3306")),
        database=os.environ["MARIADB_DATABASE"],
        user=os.environ["MARIADB_PUBLISH_USER"],
        password=os.environ["MARIADB_PUBLISH_PASSWORD"],
        charset="utf8mb4",
        autocommit=False,
        cursorclass=DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT f.snapshot_id,s.symbol,DATE(f.as_of_utc) as_of_date,f.feature_json,
                       l.target_before_stop,l.outcome
                FROM fact_decision_feature_snapshot f
                JOIN fact_decision_label l ON l.snapshot_id=f.snapshot_id
                JOIN dim_symbol s ON s.symbol_id=f.symbol_id
                WHERE f.certification_status='CERTIFIED' AND l.entry_filled=TRUE
                  AND l.horizon_sessions=10 AND s.symbol<>'SPY'
                ORDER BY f.as_of_utc,s.symbol
                """
            )
            rows = []
            for row in cursor.fetchall():
                payload = (
                    row["feature_json"]
                    if isinstance(row["feature_json"], dict)
                    else json.loads(row["feature_json"])
                )
                realized_r = 2.0 if row["outcome"] in {"TARGET_1", "TARGET_2"} else -1.0
                rows.append(
                    TrainingRow(
                        row["snapshot_id"],
                        row["symbol"],
                        row["as_of_date"],
                        feature_values(payload),
                        int(row["target_before_stop"]),
                        realized_r,
                    )
                )
            model, result = train_walk_forward(rows)
            medians = [
                statistics.median(row.features[index] for row in rows)
                for index in range(len(rows[0].features))
            ]
            artifact = io.BytesIO()
            joblib.dump(
                {"model": model, "feature_names": list(FEATURE_NAMES), "medians": medians},
                artifact,
            )
            payload = artifact.getvalue()
            manifest = artifact_manifest(
                model_version=args.model_version, result=result, payload=payload
            )
            key = f"decision-intelligence/{args.model_version}/model.joblib"
            s3 = boto3.client(
                "s3",
                endpoint_url=os.environ["MINIO_ENDPOINT"],
                aws_access_key_id=os.environ["MINIO_ROOT_USER"],
                aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
            )
            try:
                s3.head_bucket(Bucket=args.models_bucket)
            except Exception:
                s3.create_bucket(Bucket=args.models_bucket)
            s3.put_object(
                Bucket=args.models_bucket,
                Key=key,
                Body=payload,
                ContentType="application/octet-stream",
            )
            s3.put_object(
                Bucket=args.models_bucket,
                Key=f"decision-intelligence/{args.model_version}/manifest.json",
                Body=(json.dumps(manifest, sort_keys=True) + "\n").encode(),
                ContentType="application/json",
            )
            metrics = manifest["metrics"]
            cursor.execute(
                """
                INSERT INTO decision_model_registry (
                    model_version,model_family,status,artifact_uri,artifact_sha256,
                    feature_schema_version,trained_from_date,trained_through_date,
                    activation_threshold,calibration_method,promotion_eligible,
                    promotion_reasons_json,metrics_json,training_run_id,code_version
                ) VALUES (%s,%s,'PREVIEW',%s,%s,2,%s,%s,%s,'sigmoid',%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE artifact_uri=VALUES(artifact_uri),
                    artifact_sha256=VALUES(artifact_sha256),metrics_json=VALUES(metrics_json),
                    promotion_eligible=VALUES(promotion_eligible),
                    promotion_reasons_json=VALUES(promotion_reasons_json)
                """,
                (
                    args.model_version,
                    result.model_family,
                    f"s3://{args.models_bucket}/{key}",
                    manifest["artifact_sha256"],
                    min(row.as_of_date for row in rows),
                    max(row.as_of_date for row in rows),
                    result.activation_threshold,
                    result.promotion_eligible,
                    json.dumps(list(result.promotion_reasons)),
                    json.dumps(metrics),
                    args.run_id,
                    os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
                ),
            )
        connection.commit()
        print(
            json.dumps(
                {
                    "event": "hybrid_model_registered",
                    "model_version": args.model_version,
                    "status": "PREVIEW",
                }
            )
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
