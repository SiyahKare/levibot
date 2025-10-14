"""
Tests for recovery policy.
"""

import time

from src.engine.recovery import RecoveryPolicy


def test_recovery_policy_basic():
    """Test basic recovery policy."""
    policy = RecoveryPolicy(max_restarts_per_hour=3, backoff_base=1)
    
    # First restart should be allowed
    assert policy.should_recover("TEST") is True
    
    # Second restart should be allowed (after backoff)
    time.sleep(1.1)
    assert policy.should_recover("TEST") is True
    
    # Third restart should be allowed (after backoff)
    time.sleep(2.1)
    assert policy.should_recover("TEST") is True
    
    # Fourth restart should be denied (max reached)
    time.sleep(4.1)
    assert policy.should_recover("TEST") is False


def test_recovery_policy_reset():
    """Test recovery policy reset."""
    policy = RecoveryPolicy(max_restarts_per_hour=2, backoff_base=1)
    
    policy.should_recover("TEST")
    time.sleep(1.1)
    policy.should_recover("TEST")
    
    # Should be at limit
    time.sleep(2.1)
    assert policy.should_recover("TEST") is False
    
    # Reset
    policy.reset("TEST")
    
    # Should work again
    assert policy.should_recover("TEST") is True


def test_recovery_policy_multiple_symbols():
    """Test recovery policy with multiple symbols."""
    policy = RecoveryPolicy(max_restarts_per_hour=2, backoff_base=1)
    
    # Symbol A
    assert policy.should_recover("A") is True
    time.sleep(1.1)
    assert policy.should_recover("A") is True
    
    # Symbol B (independent)
    assert policy.should_recover("B") is True
    time.sleep(1.1)
    assert policy.should_recover("B") is True

