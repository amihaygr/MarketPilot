"""Alpaca adapter reserved for Phase 6 external-source integration."""

import json
import os
from decimal import Decimal
from uuid import uuid4

from alpaca.data.live import StockDataStream
from confluent_kafka import Producer

from marketpilot.contracts.market_bar import MarketBarV1
from marketpilot.core.settings import Settings


def run_alpaca(settings: Settings, producer: Producer) -> None:
    stream = StockDataStream(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_API_SECRET"])

    async def on_bar(bar: object) -> None:
        event = MarketBarV1(
            event_id=uuid4(),
            symbol=str(bar.symbol).upper(),
            event_time_utc=bar.timestamp,
            interval=settings.market_bar_interval,
            open=Decimal(str(bar.open)),
            high=Decimal(str(bar.high)),
            low=Decimal(str(bar.low)),
            close=Decimal(str(bar.close)),
            volume=int(bar.volume),
        ).to_event()
        producer.produce(
            settings.market_bars_topic,
            key=event["symbol"],
            value=json.dumps(event, separators=(",", ":")),
        )
        producer.poll(0)

    stream.subscribe_bars(on_bar, *settings.symbols)
    stream.run()
