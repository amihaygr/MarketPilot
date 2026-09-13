import json
from datetime import date, datetime
from decimal import Decimal

from marketpilot.corporate_actions.adjustments import adjust_bars_for_splits
from marketpilot.corporate_actions.client import AlpacaCorporateActionsClient
from marketpilot.corporate_actions.ingestion import flatten_actions


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = json.dumps(payload).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_client_pages_and_flattens_versioned_response() -> None:
    requests = []

    def opener(request, **_kwargs):
        requests.append(request)
        return FakeResponse(
            {
                "corporate_actions": {
                    "forward_splits": [
                        {"id": "ca-1", "symbol": "AAPL", "process_date": "2026-01-01"}
                    ]
                },
                "next_page_token": None,
            }
        )

    client = AlpacaCorporateActionsClient(
        base_url="https://data.alpaca.markets/v1/corporate-actions",
        api_key="key",
        api_secret="secret",
        opener=opener,
        sleep=lambda _seconds: None,
    )
    pages = list(client.pages(symbols=("AAPL",), start=date(2026, 1, 1), end=date(2026, 1, 2)))

    assert len(pages) == 1
    assert flatten_actions(pages[0].decoded)[0]["action_type"] == "forward_splits"
    assert requests[0].get_header("Apca-api-secret-key") == "secret"


def test_split_adjustment_changes_pre_split_copy_only() -> None:
    source = [
        {
            "event_time_utc": datetime(2026, 1, 1, 15),
            "open_price": Decimal("100"),
            "high_price": Decimal("104"),
            "low_price": Decimal("96"),
            "close_price": Decimal("102"),
            "volume": 100,
        }
    ]
    adjusted = adjust_bars_for_splits(
        source,
        [
            {
                "action_type": "forward_splits",
                "ex_date": date(2026, 1, 2),
                "old_rate": 1,
                "new_rate": 4,
            }
        ],
    )

    assert adjusted[0]["close_price"] == Decimal("25.5")
    assert adjusted[0]["volume"] == 400
    assert source[0]["close_price"] == Decimal("102")
