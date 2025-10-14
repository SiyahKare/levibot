"""
Tests for risk management system.
"""

from src.risk.manager import RiskManager
from src.risk.policy import RiskPolicy


def test_global_stop_trigger():
    """Test global stop loss triggers at threshold."""
    rm = RiskManager(RiskPolicy(max_daily_loss_pct=1.0), base_equity=10000.0)

    # Lose 1.5% (150 USD)
    rm.update_equity(realized_delta=-150.0)

    # Should trigger global stop
    assert rm.realized_today_pct() < -1.0
    assert rm.is_global_stop() is True


def test_global_stop_no_trigger():
    """Test global stop doesn't trigger below threshold."""
    rm = RiskManager(RiskPolicy(max_daily_loss_pct=3.0), base_equity=10000.0)

    # Lose 1% (100 USD)
    rm.update_equity(realized_delta=-100.0)

    # Should NOT trigger global stop
    assert rm.realized_today_pct() == -1.0
    assert rm.is_global_stop() is False


def test_position_sizing_bounds():
    """Test position sizing respects per-symbol cap."""
    rm = RiskManager(RiskPolicy(max_symbol_risk_pct=0.2, kelly_fraction=0.5))

    # High probability, high confidence
    size = rm.calc_position_size(
        "BTCUSDT", prob_up=0.65, confidence=0.8, vol_annual=0.5
    )

    # Should be capped at max_symbol_risk_pct
    assert 0.0 <= size <= 0.2


def test_position_sizing_scales_with_confidence():
    """Test position size increases with confidence."""
    rm = RiskManager(RiskPolicy())

    # Low confidence
    size_low = rm.calc_position_size(
        "BTCUSDT", prob_up=0.55, confidence=0.1, vol_annual=0.5
    )

    # High confidence
    size_high = rm.calc_position_size(
        "BTCUSDT", prob_up=0.55, confidence=0.9, vol_annual=0.5
    )

    # High confidence should result in larger size
    assert size_high > size_low


def test_concurrent_positions_limit():
    """Test concurrent position limit."""
    rm = RiskManager(RiskPolicy(max_concurrent_positions=2))

    # First position - should be allowed
    assert rm.can_open_new_position("A") is True
    rm.on_order_filled("A", "long", 1000.0)

    # Second position - should be allowed
    assert rm.can_open_new_position("B") is True
    rm.on_order_filled("B", "long", 1000.0)

    # Third position - should be blocked
    assert rm.can_open_new_position("C") is False


def test_concurrent_positions_after_close():
    """Test concurrent positions after closing one."""
    rm = RiskManager(RiskPolicy(max_concurrent_positions=2))

    # Open 2 positions
    rm.on_order_filled("A", "long", 1000.0)
    rm.on_order_filled("B", "long", 1000.0)

    # Should be at limit
    assert rm.can_open_new_position("C") is False

    # Close one position
    rm.on_position_closed("A", realized_pnl=50.0)

    # Should be able to open again
    assert rm.can_open_new_position("C") is True


def test_equity_tracking():
    """Test equity tracking with realized PnL."""
    rm = RiskManager(base_equity=10000.0)

    # Initial equity
    assert rm.book.equity_now == 10000.0

    # Win a trade (+100)
    rm.on_order_filled("A", "long", 1000.0, realized_pnl=100.0)
    assert rm.book.equity_now == 10100.0

    # Lose a trade (-50)
    rm.on_position_closed("A", realized_pnl=-50.0)
    assert rm.book.equity_now == 10050.0


def test_day_reset():
    """Test daily reset functionality."""
    rm = RiskManager(base_equity=10000.0)

    # Make some profit
    rm.update_equity(realized_delta=500.0)
    assert rm.book.equity_now == 10500.0
    assert rm.realized_today_pct() == 5.0

    # Reset day
    rm.on_day_reset()

    # Equity should stay, but daily tracking resets
    assert rm.book.equity_now == 10500.0
    assert rm.book.equity_start_day == 10500.0
    assert rm.realized_today_pct() == 0.0


def test_kelly_sizing():
    """Test Kelly criterion sizing."""
    rm = RiskManager()

    # Even odds (50/50)
    kelly_even = rm._kelly_size(prob_up=0.5, risk_reward=1.0)
    assert kelly_even == 0.0  # No edge

    # Edge (60% win rate)
    kelly_edge = rm._kelly_size(prob_up=0.6, risk_reward=1.0)
    assert kelly_edge > 0.0  # Positive edge

    # Strong edge (70% win rate)
    kelly_strong = rm._kelly_size(prob_up=0.7, risk_reward=1.0)
    assert kelly_strong > kelly_edge  # Stronger edge


def test_vol_scaling():
    """Test volatility-based scaling."""
    rm = RiskManager()

    # Low vol -> scale up
    scale_low = rm._vol_position_scale(vol_annual=0.1, vol_target_ann=0.15)
    assert scale_low > 1.0

    # High vol -> scale down
    scale_high = rm._vol_position_scale(vol_annual=0.8, vol_target_ann=0.15)
    assert scale_high < 1.0


def test_summary():
    """Test risk manager summary."""
    rm = RiskManager(base_equity=10000.0)

    summary = rm.summary()

    assert "equity_now" in summary
    assert "equity_start_day" in summary
    assert "realized_today_pct" in summary
    assert "positions_open" in summary
    assert "global_stop" in summary
    assert "policy" in summary

    assert summary["equity_now"] == 10000.0
    assert summary["positions_open"] == 0
    assert summary["global_stop"] is False
