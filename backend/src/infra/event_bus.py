"""
Event Bus - Redis Streams based message broker
Handles all inter-service communication with guaranteed delivery
"""

import json
import time
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from typing import Any

import redis.asyncio as aioredis


@dataclass
class Event:
    """Base event structure"""

    event_id: str
    event_type: str
    timestamp: float
    payload: dict[str, Any]
    source: str
    version: str = "1.0"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(**data)


class EventBus:
    """
    Redis Streams based event bus with consumer groups

    Features:
    - Guaranteed delivery (XACK)
    - Consumer groups for load balancing
    - Dead letter queue for failed messages
    - Message TTL and cleanup
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: aioredis.Redis | None = None
        self._consumer_group = "levibot-workers"

    async def connect(self):
        """Initialize Redis connection"""
        if self._client is None:
            self._client = await aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )

    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None

    async def publish(
        self, stream: str, event_type: str, payload: dict, source: str = "levibot"
    ) -> str:
        """
        Publish event to stream

        Args:
            stream: Stream name (e.g., "signals", "orders", "alerts")
            event_type: Event type identifier
            payload: Event data
            source: Source service name

        Returns:
            Message ID
        """
        await self.connect()

        event = Event(
            event_id=f"{int(time.time() * 1000)}",
            event_type=event_type,
            timestamp=time.time(),
            payload=payload,
            source=source,
        )

        msg_id = await self._client.xadd(
            f"stream:{stream}",
            {"data": json.dumps(event.to_dict())},
            maxlen=10000,  # Keep last 10k messages
        )

        return msg_id

    async def subscribe(
        self, stream: str, consumer_name: str, block_ms: int = 5000, count: int = 10
    ) -> AsyncIterator[Event]:
        """
        Subscribe to stream with consumer group

        Args:
            stream: Stream name
            consumer_name: Unique consumer identifier
            block_ms: Block timeout in milliseconds
            count: Max messages per read

        Yields:
            Event objects
        """
        await self.connect()
        stream_key = f"stream:{stream}"

        # Create consumer group if not exists
        try:
            await self._client.xgroup_create(
                stream_key, self._consumer_group, id="0", mkstream=True
            )
        except aioredis.ResponseError:
            pass  # Group already exists

        while True:
            try:
                # Read from stream
                messages = await self._client.xreadgroup(
                    self._consumer_group,
                    consumer_name,
                    {stream_key: ">"},
                    count=count,
                    block=block_ms,
                )

                if not messages:
                    continue

                for stream_name, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        try:
                            event_dict = json.loads(msg_data["data"])
                            event = Event.from_dict(event_dict)

                            yield event

                            # Acknowledge message
                            await self._client.xack(
                                stream_key, self._consumer_group, msg_id
                            )

                        except Exception as e:
                            print(f"❌ Failed to process message {msg_id}: {e}")
                            # Move to DLQ
                            await self._move_to_dlq(stream, msg_id, msg_data, str(e))

            except Exception as e:
                print(f"❌ Stream read error: {e}")
                await asyncio.sleep(1)

    async def _move_to_dlq(self, stream: str, msg_id: str, msg_data: dict, error: str):
        """Move failed message to dead letter queue"""
        dlq_key = f"dlq:{stream}"
        await self._client.xadd(
            dlq_key,
            {
                "original_id": msg_id,
                "data": json.dumps(msg_data),
                "error": error,
                "timestamp": time.time(),
            },
            maxlen=1000,
        )

    async def get_stream_info(self, stream: str) -> dict:
        """Get stream statistics"""
        await self.connect()
        stream_key = f"stream:{stream}"

        try:
            info = await self._client.xinfo_stream(stream_key)
            groups = await self._client.xinfo_groups(stream_key)

            return {
                "length": info["length"],
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "groups": [
                    {
                        "name": g["name"],
                        "consumers": g["consumers"],
                        "pending": g["pending"],
                    }
                    for g in groups
                ],
            }
        except aioredis.ResponseError:
            return {"error": "Stream not found"}

    async def trim_stream(self, stream: str, maxlen: int = 10000):
        """Trim stream to max length"""
        await self.connect()
        await self._client.xtrim(f"stream:{stream}", maxlen=maxlen)


# Convenience functions for common streams
async def publish_signal(
    bus: EventBus,
    symbol: str,
    side: int,
    confidence: float,
    strategy: str,
    reason: str,
    metadata: dict | None = None,
):
    """Publish trading signal"""
    await bus.publish(
        "signals",
        "signal.new",
        {
            "symbol": symbol,
            "side": side,
            "confidence": confidence,
            "strategy": strategy,
            "reason": reason,
            "metadata": metadata or {},
        },
    )


async def publish_order(
    bus: EventBus,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
    metadata: dict | None = None,
):
    """Publish order request"""
    await bus.publish(
        "orders",
        "order.create",
        {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "price": price,
            "metadata": metadata or {},
        },
    )


async def publish_alert(
    bus: EventBus, level: str, title: str, message: str, metadata: dict | None = None
):
    """Publish alert/notification"""
    await bus.publish(
        "alerts",
        f"alert.{level}",
        {
            "level": level,
            "title": title,
            "message": message,
            "metadata": metadata or {},
        },
    )


import asyncio

if __name__ == "__main__":
    # Test event bus
    async def test():
        bus = EventBus("redis://localhost:6379/0")

        # Publish test event
        await publish_signal(
            bus,
            symbol="BTCUSDT",
            side=1,
            confidence=0.65,
            strategy="lse",
            reason="momentum_breakout",
        )

        print("✅ Published test signal")

        # Subscribe and consume
        async for event in bus.subscribe("signals", "test-consumer"):
            print(f"📨 Received: {event.event_type} - {event.payload}")
            break

        await bus.disconnect()

    asyncio.run(test())
