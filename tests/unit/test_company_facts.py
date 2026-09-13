from marketpilot.sec.company_facts import normalize_company_facts


def test_company_facts_keeps_latest_filing_and_does_not_invent_missing_metrics() -> None:
    payload = {
        "facts": {
            "us-gaap": {
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {
                                "form": "10-Q",
                                "filed": "2026-05-01",
                                "end": "2026-03-31",
                                "val": 10,
                                "accn": "old",
                            },
                            {
                                "form": "10-Q",
                                "filed": "2026-05-03",
                                "end": "2026-03-31",
                                "val": 11,
                                "accn": "new",
                            },
                        ]
                    }
                }
            }
        }
    }
    facts = normalize_company_facts(payload)
    assert len(facts) == 1
    assert facts[0].metric_code == "NET_INCOME"
    assert str(facts[0].value) == "11"
    assert facts[0].accession_number == "new"
