"""
LSE Engine - Low-latency Scalp Engine
v1.0 with paper portfolio executor
"""
import threading
import time

import numpy as np

from ..base import Mode, StrategyEngine
from .config import StrategyConfig
from .executor import LSEExecutor
from .features import FeatureCache, calculate_atr, calculate_spread_bps, calculate_zscore
from .guards import TradingGuards
from .price_guards import PriceGuard


class LSEEngine(StrategyEngine):
    """LSE Strategy Engine"""
    
    name = "lse"
    
    def __init__(self):
        self._cfg = StrategyConfig()
        self._running = False
        self._mode: Mode = "paper"
        self._thread: threading.Thread | None = None
        self._last_loop_ms = None
        
        # Executor (paper portfolio integration)
        self._executor: LSEExecutor | None = None
        
        # Features & Guards
        self._features = FeatureCache()
        self._guards = TradingGuards(self._cfg.filters)
        self._price_guard = PriceGuard(symbol=self._cfg.symbol)
        
        # Mock market data (will be replaced with real feed)
        self._mock_prices = np.array([50000.0])
        self._mock_bid = 50000.0
        self._mock_ask = 50001.0
        
        # Trade log (in-memory for debugging)
        self._trade_log = []
    
    def start(self, mode: Mode | None = None, overrides: dict | None = None) -> None:
        """Start the engine"""
        if self._running:
            return
        
        if mode:
            self._mode = mode
        if overrides:
            self.update_params(overrides)
        
        # Initialize executor
        self._executor = LSEExecutor(symbol=self._cfg.symbol, mode=self._mode)
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the engine"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
    
    def running(self) -> bool:
        """Check if running"""
        return self._running
    
    def params(self) -> dict:
        """Get current parameters"""
        return {
            "symbol": self._cfg.symbol,
            "mode": self._mode,
            "leverage": self._cfg.leverage,
            "quote_budget": self._cfg.quote_budget,
            "windows": self._cfg.windows,
            "atr": self._cfg.atr,
            "zscore": self._cfg.zscore,
            "risk": self._cfg.risk,
            "filters": self._cfg.filters,
            "recording": self._cfg.recording,
        }
    
    def update_params(self, p: dict) -> dict:
        """Update parameters"""
        for k, v in p.items():
            if hasattr(self._cfg, k):
                setattr(self._cfg, k, v)
        return self.params()
    
    def _run_loop(self):
        """Main engine loop with real executor"""
        while self._running:
            t0 = time.perf_counter()
            
            # Tick processing (4 Hz stub - real will be WS-driven)
            time.sleep(0.25)
            
            # 1. Update mock market data
            self._update_mock_data()
            current_price = self._mock_bid  # Use bid for long entries
            
            # 2. Calculate features
            current_ts = time.time()
            if self._features.is_stale(current_ts, ttl_sec=1.0):
                self._calculate_features(current_ts)
            
            # 3. Check guards
            spread_bps = calculate_spread_bps(self._mock_bid, self._mock_ask)
            vol_bps = self._features.vol or 10.0
            
            # Get current portfolio stats for DD calculation
            if self._executor:
                portfolio_stats = self._executor.get_portfolio_stats()
                current_dd = portfolio_stats.get("total_pnl_pct", 0) / 100.0
                open_count = portfolio_stats.get("num_positions", 0)
            else:
                current_dd = 0.0
                open_count = 0
            
            guard_result = self._guards.check_all(
                vol_bps=vol_bps,
                spread_bps=spread_bps,
                latency_ms=self._last_loop_ms or 0,
                current_dd=current_dd,
                open_count=open_count
            )
            
            # 4. Position management with real executor
            if self._executor:
                # Check stop loss / take profit first
                if self._executor.has_position():
                    sl_bps = self._cfg.risk.get("hard_stop_bps", 15)
                    tp_bps = self._cfg.risk.get("take_profit_bps", 25)
                    
                    sl_result = self._executor.check_stop_loss(
                        current_price,
                        sl_pct=sl_bps / 10000.0
                    )
                    if sl_result:
                        self._trade_log.append(sl_result)
                        # Persist to DB
                        try:
                            from ..db.trades_repo import TradesRepository
                            TradesRepository.log_trade(
                                strategy="lse",
                                symbol=sl_result["symbol"],
                                side="long",
                                action="exit_position",
                                price=sl_result["exit_price"],
                                qty=sl_result["qty"],
                                pnl_usd=sl_result["pnl_usd"],
                                pnl_pct=sl_result["pnl_pct"],
                                reason=sl_result["reason"],
                                mode=self._mode
                            )
                        except Exception as e:
                            print(f"⚠️ Failed to log SL to DB: {e}")
                    
                    tp_result = self._executor.check_take_profit(
                        current_price,
                        tp_pct=tp_bps / 10000.0
                    )
                    if tp_result:
                        self._trade_log.append(tp_result)
                        # Persist to DB
                        try:
                            from ..db.trades_repo import TradesRepository
                            TradesRepository.log_trade(
                                strategy="lse",
                                symbol=tp_result["symbol"],
                                side="long",
                                action="exit_position",
                                price=tp_result["exit_price"],
                                qty=tp_result["qty"],
                                pnl_usd=tp_result["pnl_usd"],
                                pnl_pct=tp_result["pnl_pct"],
                                reason=tp_result["reason"],
                                mode=self._mode
                            )
                        except Exception as e:
                            print(f"⚠️ Failed to log TP to DB: {e}")
                
                # 5. Signal generation & entry
                if guard_result.passed and not self._executor.has_position():
                    # Entry signal logic (simplified - based on z-score)
                    zscore = self._features.zscore or 0.0
                    atr = self._features.atr or 0.0
                    
                    z_enter = self._cfg.zscore.get("z_enter", 1.5)
                    atr_k = self._cfg.atr.get("k_enter", 0.8)
                    
                    # Entry condition: high z-score + sufficient ATR
                    if abs(zscore) > z_enter and atr > current_price * atr_k / 10000:
                        # Calculate position size
                        notional_usd = self._cfg.quote_budget * self._cfg.leverage
                        qty = notional_usd / current_price
                        
                        # Enter long
                        result = self._executor.enter_long(
                            price=current_price,
                            qty=qty,
                            reason=f"zscore={zscore:.2f} atr={atr:.2f}"
                        )
                        self._trade_log.append(result)
                        
                        # Persist to DB
                        try:
                            from ..db.trades_repo import TradesRepository
                            TradesRepository.log_trade(
                                strategy="lse",
                                symbol=result["symbol"],
                                side="long",
                                action="enter_long",
                                price=result["price"],
                                qty=result["qty"],
                                notional_usd=result["notional_usd"],
                                reason=result["reason"],
                                mode=self._mode
                            )
                        except Exception as e:
                            print(f"⚠️ Failed to log trade to DB: {e}")
            
            self._last_loop_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    def _update_mock_data(self):
        """Update mock market data (stub)"""
        # Random walk
        change = np.random.randn() * 10
        new_price = self._mock_prices[-1] + change
        self._mock_prices = np.append(self._mock_prices[-200:], new_price)
        self._mock_bid = new_price - 0.5
        self._mock_ask = new_price + 0.5
    
    def _calculate_features(self, ts: float):
        """Calculate features from price data"""
        if len(self._mock_prices) < 20:
            return
        
        # Mock OHLC for ATR
        high = self._mock_prices[-14:] + 1
        low = self._mock_prices[-14:] - 1
        close = self._mock_prices[-14:]
        
        atr = calculate_atr(high, low, close, period=self._cfg.atr["period"])
        zscore = calculate_zscore(self._mock_prices, lookback=min(120, len(self._mock_prices)))
        
        # Realized vol
        returns = np.diff(self._mock_prices) / self._mock_prices[:-1]
        vol = np.std(returns[-60:]) * 10000 if len(returns) > 60 else 10.0
        
        self._features.update(ts=ts, atr=atr, zscore=zscore, vol=vol)
    
    def health(self) -> dict:
        """Get health status with real-time guards and position info"""
        spread_bps = calculate_spread_bps(self._mock_bid, self._mock_ask)
        vol_bps = self._features.vol or 10.0
        
        # Get current portfolio stats
        if self._executor:
            portfolio_stats = self._executor.get_portfolio_stats()
            current_dd = portfolio_stats.get("total_pnl_pct", 0) / 100.0
            open_count = portfolio_stats.get("num_positions", 0)
            
            # Get current position PnL
            position_pnl = self._executor.get_position_pnl(self._mock_bid)
        else:
            current_dd = 0.0
            open_count = 0
            portfolio_stats = {}
            position_pnl = {"has_position": False}
        
        guard_status = self._guards.status(
            vol_bps=vol_bps,
            spread_bps=spread_bps,
            latency_ms=self._last_loop_ms or 0,
            current_dd=current_dd,
            open_count=open_count
        )
        
        return {
            "running": self._running,
            "mode": self._mode,
            "symbol": self._cfg.symbol,
            "latency_ms": self._last_loop_ms,
            "guards": guard_status,
            "features": {
                "atr": self._features.atr,
                "zscore": self._features.zscore,
                "vol_bps": self._features.vol,
                "spread_bps": spread_bps,
            },
            "position": position_pnl,
            "portfolio": {
                "equity": portfolio_stats.get("equity", 0.0),
                "cash_balance": portfolio_stats.get("cash_balance", 0.0),
                "total_pnl": portfolio_stats.get("total_pnl", 0.0),
                "win_rate": portfolio_stats.get("win_rate", 0.0)
            }
        }
    
    def pnl(self) -> dict:
        """Get PnL from executor/portfolio"""
        if self._executor:
            stats = self._executor.get_portfolio_stats()
            return {
                "realized_pnl": stats.get("total_pnl", 0.0),
                "realized_pnl_pct": stats.get("total_pnl_pct", 0.0),
                "trades": stats.get("num_trades", 0),
                "win_rate": stats.get("win_rate", 0.0),
                "equity": stats.get("equity", 0.0),
                "cash_balance": stats.get("cash_balance", 0.0)
            }
        
        return {
            "realized_pnl": 0.0,
            "trades": 0
        }
    
    def trades_recent(self, limit: int = 100) -> list:
        """Get recent trades from log"""
        return list(reversed(self._trade_log))[:limit]


# Singleton instance
ENGINE = LSEEngine()

