# Codex First-Run Prompts

Use these prompts in order. Do not combine all phases into one request.

## Prompt 1 - Verify project context

```text
Read AGENTS.md and all files under docs/.

Then inspect the complete repository.

Do not modify files yet.

Return:
1. The instruction files you loaded.
2. Your understanding of the project goal.
3. The required live data flow.
4. The required Bronze to Silver to Gold flow.
5. What Airflow is allowed to execute.
6. Which services must remain long-running.
7. How automatic streaming starts and recovers.
8. The planned storage responsibilities.
9. Missing repository components.
10. Architecture conflicts, ambiguities, and implementation risks.

Explicitly list the Mermaid and ADR files you used.
```

## Prompt 2 - Plan Phase 1

```text
Using AGENTS.md, the accepted ADRs, and docs/implementation-plan.md, create a detailed plan for Phase 1 only.

Phase 1 scope:
- Docker Compose
- Kafka in KRaft mode
- MariaDB
- MinIO
- Spark Master
- one Spark Worker
- internal Docker networks
- named volumes
- healthchecks
- .env.example integration
- developer README commands

Do not implement anything yet.

For every service specify:
- responsibility
- pinned image or Dockerfile strategy
- ports
- internal and published exposure
- volumes
- healthcheck
- readiness dependencies
- environment variables
- initial CPU and memory assumptions

Identify compatibility risks, especially Spark packages, Kafka mode, MinIO S3A support, healthcheck tooling, and host resource usage.
```

## Prompt 3 - Implement Phase 1

```text
Implement the approved Phase 1 plan only.

Requirements:
- Do not add Airflow yet.
- Do not add Alpaca or SEC yet.
- Do not add API or Web App services yet.
- Use pinned compatible image versions.
- Add named volumes and internal networks.
- Add healthchecks.
- Use service_healthy for readiness-sensitive dependencies.
- Read safe values from .env and preserve .env.example placeholders.
- Do not commit real secrets.
- Add or update README instructions.
- Validate with docker compose config.
- If Docker is available, start the stack and verify health.
- Fix validation failures before finishing.

Return:
- changed files
- commands executed
- validation results
- services not tested
- remaining risks
```

## Prompt 4 - Review the implementation

```text
Review the current Git diff as a senior data platform engineer.

Do not edit files.

Check:
- consistency with AGENTS.md and accepted ADRs
- Docker Compose validity
- healthcheck correctness
- startup readiness versus container start order
- persistent volumes
- secrets exposure
- published ports
- restart behavior
- version compatibility
- Windows and Docker Desktop usability
- missing tests and documentation

Report findings by severity and include exact file references.
```

## Prompt 5 - First vertical slice

```text
Plan the synthetic market-bar vertical slice.

Target flow:
synthetic producer -> Kafka -> raw archive sink -> MinIO Bronze
synthetic producer -> Kafka -> Spark Structured Streaming -> MariaDB Gold

Do not implement yet.

Define:
- event schema and versioning
- topic and key strategy
- Bronze object layout
- checkpoint strategy
- MariaDB business key and upsert behavior
- malformed-event path
- integration-test approach
- restart and duplicate-delivery tests
- acceptance criteria
```
