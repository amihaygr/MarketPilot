"""Normalize selected, filed SEC US-GAAP facts without inventing missing values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

CONCEPTS = {
    "REVENUE": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"),
    "NET_INCOME": ("NetIncomeLoss",),
    "EPS_DILUTED": ("EarningsPerShareDiluted",),
    "OPERATING_CASH_FLOW": ("NetCashProvidedByUsedInOperatingActivities",),
    "CAPEX": ("PaymentsToAcquirePropertyPlantAndEquipment",),
    "CASH": ("CashAndCashEquivalentsAtCarryingValue",),
    "DEBT": ("LongTermDebtCurrent", "LongTermDebtNoncurrent"),
    "EQUITY": ("StockholdersEquity",),
    "SHARES_DILUTED": ("WeightedAverageNumberOfDilutedSharesOutstanding",),
}


@dataclass(frozen=True, slots=True)
class FundamentalFact:
    metric_code: str
    period_end: date
    filed_at_utc: datetime
    value: Decimal
    unit: str
    form: str
    accession_number: str | None


def normalize_company_facts(payload: dict[str, Any]) -> list[FundamentalFact]:
    us_gaap = payload.get("facts", {}).get("us-gaap", {})
    normalized: dict[tuple[str, date, str], FundamentalFact] = {}
    for metric, candidates in CONCEPTS.items():
        for concept in candidates:
            units = us_gaap.get(concept, {}).get("units", {})
            for unit, observations in units.items():
                for item in observations:
                    if (
                        item.get("form") not in {"10-K", "10-Q"}
                        or not item.get("filed")
                        or not item.get("end")
                    ):
                        continue
                    fact = FundamentalFact(
                        metric_code=metric,
                        period_end=date.fromisoformat(item["end"]),
                        filed_at_utc=datetime.combine(
                            date.fromisoformat(item["filed"]), datetime.min.time(), tzinfo=UTC
                        ),
                        value=Decimal(str(item["val"])),
                        unit=unit,
                        form=item["form"],
                        accession_number=item.get("accn"),
                    )
                    key = (metric, fact.period_end, unit)
                    if key not in normalized or fact.filed_at_utc > normalized[key].filed_at_utc:
                        normalized[key] = fact
            if any(key[0] == metric for key in normalized):
                break
    return sorted(normalized.values(), key=lambda fact: (fact.metric_code, fact.period_end))
