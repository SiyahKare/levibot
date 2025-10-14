"""
Circuit Breaker - Auto-recovery and fault tolerance
Prevents cascade failures and enables graceful degradation
"""
import asyncio
import time
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as aioredis


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: int = 60   # Time before trying half-open
    window_seconds: int = 60    # Rolling window for failure counting


class CircuitBreaker:
    """
    Circuit breaker for service protection
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed
    
    Features:
    - Automatic recovery attempts
    - Failure rate tracking
    - Graceful degradation
    - Redis-backed state (distributed)
    """
    
    def __init__(
        self,
        name: str,
        redis_url: str,
        config: CircuitConfig | None = None
    ):
        self.name = name
        self.redis_url = redis_url
        self.config = config or CircuitConfig()
        self._client: aioredis.Redis | None = None
        
        # Local state cache
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._opened_at = 0.0
    
    async def connect(self):
        """Initialize Redis connection"""
        if self._client is None:
            self._client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self._load_state()
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def _load_state(self):
        """Load state from Redis"""
        if not self._client:
            return
        
        state_key = f"circuit:{self.name}:state"
        failures_key = f"circuit:{self.name}:failures"
        opened_key = f"circuit:{self.name}:opened_at"
        
        state_str = await self._client.get(state_key)
        if state_str:
            self._state = CircuitState(state_str)
        
        failure_count = await self._client.get(failures_key)
        if failure_count:
            self._failure_count = int(failure_count)
        
        opened_at = await self._client.get(opened_key)
        if opened_at:
            self._opened_at = float(opened_at)
    
    async def _save_state(self):
        """Save state to Redis"""
        if not self._client:
            return
        
        state_key = f"circuit:{self.name}:state"
        failures_key = f"circuit:{self.name}:failures"
        opened_key = f"circuit:{self.name}:opened_at"
        
        await self._client.set(state_key, self._state.value)
        await self._client.set(failures_key, self._failure_count)
        
        if self._state == CircuitState.OPEN:
            await self._client.set(opened_key, self._opened_at)
    
    async def call(self, func, *args, **kwargs):
        """
        Execute function through circuit breaker
        
        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        await self.connect()
        
        # Check if we should transition to half-open
        if self._state == CircuitState.OPEN:
            time_since_open = time.time() - self._opened_at
            if time_since_open >= self.config.timeout_seconds:
                await self._transition_to_half_open()
        
        # Block if circuit is open
        if self._state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN"
            )
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure()
            raise e
    
    async def _record_success(self):
        """Record successful execution"""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            
            if self._success_count >= self.config.success_threshold:
                await self._transition_to_closed()
        
        # Reset failure count on success in closed state
        if self._state == CircuitState.CLOSED:
            self._failure_count = 0
            await self._save_state()
    
    async def _record_failure(self):
        """Record failed execution"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        # Transition to open if threshold exceeded
        if self._failure_count >= self.config.failure_threshold:
            await self._transition_to_open()
        else:
            await self._save_state()
    
    async def _transition_to_open(self):
        """Transition to OPEN state"""
        self._state = CircuitState.OPEN
        self._opened_at = time.time()
        await self._save_state()
        
        print(f"🚨 Circuit breaker '{self.name}' OPENED "
              f"({self._failure_count} failures)")
    
    async def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        await self._save_state()
        
        print(f"🔄 Circuit breaker '{self.name}' HALF_OPEN (testing recovery)")
    
    async def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        await self._save_state()
        
        print(f"✅ Circuit breaker '{self.name}' CLOSED (recovered)")
    
    async def force_open(self):
        """Manually open circuit"""
        await self._transition_to_open()
    
    async def force_close(self):
        """Manually close circuit"""
        await self._transition_to_closed()
    
    async def reset(self):
        """Reset circuit breaker"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = 0.0
        await self._save_state()
        
        print(f"🔄 Circuit breaker '{self.name}' RESET")
    
    def get_state(self) -> dict:
        """Get circuit breaker state"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "opened_at": self._opened_at,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds
            }
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """
    Manage multiple circuit breakers
    
    Features:
    - Centralized circuit breaker registry
    - Health monitoring
    - Auto-recovery coordination
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._breakers: dict[str, CircuitBreaker] = {}
    
    def register(
        self,
        name: str,
        config: CircuitConfig | None = None
    ) -> CircuitBreaker:
        """Register a circuit breaker"""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name,
                self.redis_url,
                config
            )
        return self._breakers[name]
    
    def get(self, name: str) -> CircuitBreaker | None:
        """Get circuit breaker by name"""
        return self._breakers.get(name)
    
    async def get_all_states(self) -> dict[str, dict]:
        """Get states of all circuit breakers"""
        states = {}
        for name, breaker in self._breakers.items():
            await breaker.connect()
            states[name] = breaker.get_state()
        return states
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self._breakers.values():
            await breaker.reset()


# Global instance
_manager: CircuitBreakerManager | None = None


def get_circuit_breaker_manager(
    redis_url: str = "redis://localhost:6379/0"
) -> CircuitBreakerManager:
    """Get global circuit breaker manager"""
    global _manager
    if _manager is None:
        _manager = CircuitBreakerManager(redis_url)
    return _manager


if __name__ == "__main__":
    async def test():
        manager = get_circuit_breaker_manager()
        
        # Register circuit breakers
        exchange_cb = manager.register("exchange_api", CircuitConfig(
            failure_threshold=3,
            timeout_seconds=30
        ))
        
        db_cb = manager.register("database", CircuitConfig(
            failure_threshold=5,
            timeout_seconds=60
        ))
        
        # Test function that fails
        async def failing_api_call():
            raise Exception("API error")
        
        # Test function that succeeds
        async def successful_api_call():
            return "success"
        
        # Simulate failures
        print("🧪 Testing circuit breaker...")
        for i in range(5):
            try:
                await exchange_cb.call(failing_api_call)
            except Exception as e:
                print(f"  Attempt {i+1}: {e}")
            await asyncio.sleep(0.5)
        
        # Circuit should be open now
        print(f"\n📊 State: {exchange_cb.get_state()}")
        
        # Try to call (should be blocked)
        try:
            await exchange_cb.call(successful_api_call)
        except CircuitBreakerOpenError as e:
            print(f"\n🚫 {e}")
        
        # Wait for timeout
        print(f"\n⏳ Waiting {exchange_cb.config.timeout_seconds}s for recovery...")
        await asyncio.sleep(exchange_cb.config.timeout_seconds + 1)
        
        # Should transition to half-open and allow test
        try:
            result = await exchange_cb.call(successful_api_call)
            print(f"\n✅ Recovery test passed: {result}")
        except Exception as e:
            print(f"\n❌ Recovery test failed: {e}")
        
        # One more success should close the circuit
        await exchange_cb.call(successful_api_call)
        print(f"\n📊 Final state: {exchange_cb.get_state()}")
        
        # Get all states
        all_states = await manager.get_all_states()
        print("\n📊 All circuit breakers:")
        for name, state in all_states.items():
            print(f"  {name}: {state['state']}")
        
        await exchange_cb.disconnect()
        await db_cb.disconnect()
    
    asyncio.run(test())

