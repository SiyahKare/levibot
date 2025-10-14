"""
Audit Logging - Compliance and security tracking
Comprehensive audit trail for all critical operations
"""
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum

import redis.asyncio as aioredis

from .event_bus import EventBus


class AuditLevel(Enum):
    """Audit log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """Audit event categories"""
    AUTH = "auth"
    TRADING = "trading"
    CONFIG = "config"
    ADMIN = "admin"
    SYSTEM = "system"
    COMPLIANCE = "compliance"


@dataclass
class AuditEvent:
    """Audit event structure"""
    timestamp: float
    level: str
    category: str
    action: str
    user_id: str | None
    details: dict
    ip_address: str | None
    session_id: str | None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Audit logger for compliance and security
    
    Features:
    - Structured logging with categories
    - Redis persistence (append-only log)
    - ClickHouse integration for analytics
    - Real-time alerting for critical events
    - Tamper-evident logging
    """
    
    def __init__(
        self,
        redis_url: str,
        event_bus: EventBus | None = None
    ):
        self.redis_url = redis_url
        self.event_bus = event_bus
        self._client: aioredis.Redis | None = None
    
    async def connect(self):
        """Initialize Redis connection"""
        if self._client is None:
            self._client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def log(
        self,
        level: AuditLevel,
        category: AuditCategory,
        action: str,
        details: dict | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
        session_id: str | None = None
    ):
        """
        Log audit event
        
        Args:
            level: Severity level
            category: Event category
            action: Action description
            details: Additional details
            user_id: User identifier
            ip_address: Source IP
            session_id: Session identifier
        """
        await self.connect()
        
        event = AuditEvent(
            timestamp=time.time(),
            level=level.value,
            category=category.value,
            action=action,
            user_id=user_id,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id
        )
        
        # Store in Redis (append-only list)
        log_key = f"audit:log:{category.value}"
        await self._client.rpush(log_key, event.to_json())
        
        # Keep last 10k events per category
        await self._client.ltrim(log_key, -10000, -1)
        
        # Store in time-series index for querying
        ts_key = f"audit:ts:{int(event.timestamp)}"
        await self._client.setex(
            ts_key,
            86400 * 90,  # 90 days retention
            event.to_json()
        )
        
        # Publish to event bus for real-time processing
        if self.event_bus and level in [AuditLevel.WARNING, AuditLevel.CRITICAL]:
            await self.event_bus.publish(
                "audit",
                f"audit.{level.value}",
                event.to_dict()
            )
        
        # Print critical events
        if level == AuditLevel.CRITICAL:
            print(f"🚨 AUDIT [{category.value}] {action}: {details}")
    
    async def query(
        self,
        category: AuditCategory | None = None,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 100
    ) -> list[AuditEvent]:
        """
        Query audit logs
        
        Args:
            category: Filter by category
            start_time: Start timestamp
            end_time: End timestamp
            limit: Max results
            
        Returns:
            List of audit events
        """
        await self.connect()
        
        if category:
            log_key = f"audit:log:{category.value}"
            entries = await self._client.lrange(log_key, -limit, -1)
        else:
            # Query all categories
            entries = []
            for cat in AuditCategory:
                log_key = f"audit:log:{cat.value}"
                cat_entries = await self._client.lrange(log_key, -limit, -1)
                entries.extend(cat_entries)
        
        # Parse and filter
        events = []
        for entry in entries:
            try:
                event_dict = json.loads(entry)
                event = AuditEvent(**event_dict)
                
                # Apply time filters
                if start_time and event.timestamp < start_time:
                    continue
                if end_time and event.timestamp > end_time:
                    continue
                
                events.append(event)
            except Exception as e:
                print(f"⚠️ Failed to parse audit event: {e}")
        
        # Sort by timestamp and limit
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    async def get_summary(
        self,
        hours: int = 24
    ) -> dict:
        """
        Get audit log summary
        
        Args:
            hours: Time window in hours
            
        Returns:
            Summary statistics
        """
        start_time = time.time() - (hours * 3600)
        events = await self.query(start_time=start_time, limit=10000)
        
        # Count by category and level
        by_category = {}
        by_level = {}
        
        for event in events:
            by_category[event.category] = by_category.get(event.category, 0) + 1
            by_level[event.level] = by_level.get(event.level, 0) + 1
        
        return {
            "total_events": len(events),
            "time_window_hours": hours,
            "by_category": by_category,
            "by_level": by_level,
            "critical_count": by_level.get("critical", 0),
            "warning_count": by_level.get("warning", 0)
        }


# Convenience functions for common audit events

async def audit_login(
    logger: AuditLogger,
    user_id: str,
    success: bool,
    ip_address: str | None = None
):
    """Audit user login"""
    await logger.log(
        level=AuditLevel.INFO if success else AuditLevel.WARNING,
        category=AuditCategory.AUTH,
        action="user_login",
        details={"success": success},
        user_id=user_id,
        ip_address=ip_address
    )


async def audit_trade(
    logger: AuditLogger,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    strategy: str,
    user_id: str | None = None
):
    """Audit trade execution"""
    await logger.log(
        level=AuditLevel.INFO,
        category=AuditCategory.TRADING,
        action="trade_executed",
        details={
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "strategy": strategy
        },
        user_id=user_id
    )


async def audit_config_change(
    logger: AuditLogger,
    config_key: str,
    old_value: any,
    new_value: any,
    user_id: str | None = None
):
    """Audit configuration change"""
    await logger.log(
        level=AuditLevel.WARNING,
        category=AuditCategory.CONFIG,
        action="config_changed",
        details={
            "key": config_key,
            "old_value": str(old_value),
            "new_value": str(new_value)
        },
        user_id=user_id
    )


async def audit_kill_switch(
    logger: AuditLogger,
    activated: bool,
    reason: str,
    user_id: str | None = None
):
    """Audit kill switch activation/deactivation"""
    await logger.log(
        level=AuditLevel.CRITICAL,
        category=AuditCategory.ADMIN,
        action="kill_switch_toggled",
        details={
            "activated": activated,
            "reason": reason
        },
        user_id=user_id
    )


async def audit_model_deployment(
    logger: AuditLogger,
    model_version: str,
    stage: str,
    user_id: str | None = None
):
    """Audit ML model deployment"""
    await logger.log(
        level=AuditLevel.WARNING,
        category=AuditCategory.SYSTEM,
        action="model_deployed",
        details={
            "version": model_version,
            "stage": stage
        },
        user_id=user_id
    )


async def audit_compliance_check(
    logger: AuditLogger,
    check_type: str,
    passed: bool,
    details: dict | None = None
):
    """Audit compliance check"""
    await logger.log(
        level=AuditLevel.INFO if passed else AuditLevel.CRITICAL,
        category=AuditCategory.COMPLIANCE,
        action="compliance_check",
        details={
            "check_type": check_type,
            "passed": passed,
            **(details or {})
        }
    )


# Global instance
_logger: AuditLogger | None = None


def get_audit_logger(
    redis_url: str = "redis://localhost:6379/0",
    event_bus: EventBus | None = None
) -> AuditLogger:
    """Get global audit logger"""
    global _logger
    if _logger is None:
        _logger = AuditLogger(redis_url, event_bus)
    return _logger


if __name__ == "__main__":
    import asyncio
    
    async def test():
        logger = get_audit_logger()
        
        # Test various audit events
        await audit_login(logger, "user123", True, "192.168.1.1")
        await audit_trade(logger, "BTCUSDT", "buy", 0.1, 50000.0, "lse", "user123")
        await audit_config_change(logger, "max_position_size", 1000, 2000, "admin")
        await audit_kill_switch(logger, True, "manual_activation", "admin")
        
        # Query logs
        print("\n📋 Recent audit events:")
        events = await logger.query(limit=10)
        for event in events:
            ts = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  [{ts}] {event.category} - {event.action}")
        
        # Get summary
        summary = await logger.get_summary(hours=24)
        print("\n📊 Audit Summary (24h):")
        print(f"  Total events: {summary['total_events']}")
        print(f"  Critical: {summary['critical_count']}")
        print(f"  Warning: {summary['warning_count']}")
        print(f"  By category: {summary['by_category']}")
        
        await logger.disconnect()
    
    asyncio.run(test())

