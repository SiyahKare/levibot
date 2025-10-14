"""
RSI + MACD Strategy Engine
"""
import logging
import time
from threading import Thread
from typing import Literal

import numpy as np

from .config import RsiMacdConfig
from .features import RsiMacdFeatureCache

logger = logging.getLogger(__name__)


class RsiMacdEngine:
    """
    RSI + MACD combined strategy engine.
    
    Entry Logic:
      1. MACD histogram crosses 0 (trend)
      2. RSI crosses 50 (momentum)
      3. Both within sync_bars window
      4. Guards pass (spread/latency/vol)
    
    Exit Logic:
      - MACD histogram reverses
      - RSI reverses through 50
      - ATR SL/TP hit
      - Timeout (bars held)
    
    Modes:
      - scalp: 1m bars, tight R (1.2x)
      - day: 15m bars, moderate R (1.5-2x)
      - swing: 4h bars, wide R (2-3x)
    """
    
    def __init__(self, config: RsiMacdConfig, mode: Literal["paper", "live"] = "paper"):
        self._cfg = config
        self._mode = mode
        self._running = False
        self._thread: Thread | None = None
        
        self._features = RsiMacdFeatureCache(max_history=200)
        
        # Position state
        self._position = {
            "side": None,  # "long" | "short" | None
            "entry_price": 0.0,
            "size": 0.0,
            "entry_bar": 0,
            "sl_price": 0.0,
            "tp_price": 0.0
        }
        
        # Trade log
        self._trade_log = []
        self._total_pnl = 0.0
        self._num_wins = 0
        self._num_losses = 0
        
        # Cooldown
        self._last_exit_bar = -999
        
        logger.info(f"RsiMacdEngine initialized: mode={mode}, symbol={config.symbol}, tf={config.tf}")
    
    def start(self) -> dict:
        """Start the strategy engine"""
        if self._running:
            return {"status": "already_running"}
        
        self._running = True
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"RsiMacdEngine started: {self._cfg.mode} mode")
        return {"status": "started", "mode": self._cfg.mode, "symbol": self._cfg.symbol}
    
    def stop(self) -> dict:
        """Stop the strategy engine"""
        if not self._running:
            return {"status": "not_running"}
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        
        logger.info("RsiMacdEngine stopped")
        return {"status": "stopped"}
    
    def health(self) -> dict:
        """Get engine health status"""
        features = self._features.get_latest()
        
        return {
            "running": self._running,
            "mode": self._cfg.mode,
            "symbol": self._cfg.symbol,
            "tf": self._cfg.tf,
            "position": self._position["side"],
            "features": features,
            "current_bar": self._features.current_bar,
            "cooldown_active": self._is_in_cooldown(),
            "total_pnl": round(self._total_pnl, 2),
            "trades": len(self._trade_log),
            "win_rate": self._calculate_win_rate()
        }
    
    def get_params(self) -> dict:
        """Get current parameters"""
        return self._cfg.to_dict()
    
    def set_params(self, params: dict) -> dict:
        """Update strategy parameters"""
        # Update config fields
        for key, value in params.items():
            if hasattr(self._cfg, key):
                setattr(self._cfg, key, value)
            elif "." in key:
                # Nested update (e.g., "rsi.period")
                parts = key.split(".")
                obj = self._cfg
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
        
        logger.info(f"RsiMacdEngine params updated: {params}")
        return {"status": "updated", "params": self._cfg.to_dict()}
    
    def pnl(self) -> dict:
        """Get PnL summary"""
        return {
            "total_pnl": round(self._total_pnl, 2),
            "num_trades": len(self._trade_log),
            "num_wins": self._num_wins,
            "num_losses": self._num_losses,
            "win_rate": self._calculate_win_rate(),
            "profit_factor": self._calculate_profit_factor()
        }
    
    def trades_recent(self, limit: int = 100) -> list[dict]:
        """Get recent trades"""
        return self._trade_log[-limit:]
    
    # ─────────────────────────────────────────────────────────────
    # Internal Logic
    # ─────────────────────────────────────────────────────────────
    
    def _run_loop(self):
        """Main strategy loop (mock data for now)"""
        base_price = 50000.0
        volatility = 300.0
        
        # Start with enough history for indicators
        init_prices = base_price + np.random.randn(100) * volatility
        for p in init_prices:
            high = p + abs(np.random.randn() * volatility * 0.3)
            low = p - abs(np.random.randn() * volatility * 0.3)
            self._features.update(
                price=p,
                high=high,
                low=low,
                rsi_period=self._cfg.rsi.period,
                macd_fast=self._cfg.macd.fast,
                macd_slow=self._cfg.macd.slow,
                macd_signal=self._cfg.macd.signal,
                atr_period=self._cfg.risk.atr_period
            )
        
        logger.info("RsiMacdEngine loop started (mock data)")
        
        while self._running:
            try:
                # Mock price update
                price = base_price + np.random.randn() * volatility
                high = price + abs(np.random.randn() * volatility * 0.3)
                low = price - abs(np.random.randn() * volatility * 0.3)
                
                # Update features
                features = self._features.update(
                    price=price,
                    high=high,
                    low=low,
                    rsi_period=self._cfg.rsi.period,
                    macd_fast=self._cfg.macd.fast,
                    macd_slow=self._cfg.macd.slow,
                    macd_signal=self._cfg.macd.signal,
                    atr_period=self._cfg.risk.atr_period
                )
                
                # Process signals
                self._process_bar(price, features)
                
                # Sleep based on mode
                sleep_time = {
                    "scalp": 1.0,   # 1 sec (mock 1m bar)
                    "day": 5.0,     # 5 sec (mock 15m bar)
                    "swing": 10.0   # 10 sec (mock 4h bar)
                }.get(self._cfg.mode, 5.0)
                
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"RsiMacdEngine loop error: {e}", exc_info=True)
                time.sleep(5.0)
    
    def _process_bar(self, price: float, features: dict):
        """Process a single bar and generate signals"""
        current_bar = self._features.current_bar
        
        # Check exits first
        if self._position["side"] is not None:
            exit_signal = self._check_exit(price, features, current_bar)
            if exit_signal:
                self._execute_exit(price, exit_signal["reason"])
                return
        
        # Check entries (if flat and not in cooldown)
        if self._position["side"] is None and not self._is_in_cooldown():
            entry_signal = self._check_entry(price, features, current_bar)
            if entry_signal:
                self._execute_entry(price, entry_signal["side"], features)
    
    def _check_entry(self, price: float, features: dict, current_bar: int) -> dict | None:
        """
        Check for entry signal.
        
        Long Entry:
          1. MACD histogram crossed above 0
          2. RSI crossed above 50
          3. Both within sync_bars window
          4. Guards OK
        """
        # Sync check
        sync_ok = (
            features["sync_bars_since_rsi"] <= self._cfg.sync_bars and
            features["sync_bars_since_macd"] <= self._cfg.sync_bars
        )
        
        if not sync_ok:
            return None
        
        # Long signal
        if features["macd_crossed_up"] or features["rsi_crossed_up"]:
            # Check if both conditions are true (or recent)
            macd_bullish = features["macd_hist"] > 0
            rsi_bullish = features["rsi"] > self._cfg.rsi.enter_above
            
            if macd_bullish and rsi_bullish:
                # TODO: Add guard checks (spread, latency, vol)
                return {"side": "long", "reason": "rsi_macd_sync"}
        
        # Short signal (optional, for swing mode)
        if self._cfg.mode == "swing":
            if features["macd_crossed_down"] or features["rsi_crossed_down"]:
                macd_bearish = features["macd_hist"] < 0
                rsi_bearish = features["rsi"] < self._cfg.rsi.enter_above
                
                if macd_bearish and rsi_bearish:
                    return {"side": "short", "reason": "rsi_macd_sync"}
        
        return None
    
    def _check_exit(self, price: float, features: dict, current_bar: int) -> dict | None:
        """
        Check for exit signal.
        
        Exit reasons:
          - MACD histogram reverses
          - RSI reverses through 50
          - ATR SL/TP hit
          - Timeout (bars held)
        """
        side = self._position["side"]
        entry_price = self._position["entry_price"]
        bars_held = current_bar - self._position["entry_bar"]
        
        # Timeout
        if bars_held >= self._cfg.risk.timeout_bars:
            return {"reason": "timeout"}
        
        # SL/TP
        if side == "long":
            if price <= self._position["sl_price"]:
                return {"reason": "stop_loss"}
            if price >= self._position["tp_price"]:
                return {"reason": "take_profit"}
            
            # Signal reversal
            if features["macd_crossed_down"] or features["rsi_crossed_down"]:
                return {"reason": "signal_reversal"}
        
        elif side == "short":
            if price >= self._position["sl_price"]:
                return {"reason": "stop_loss"}
            if price <= self._position["tp_price"]:
                return {"reason": "take_profit"}
            
            if features["macd_crossed_up"] or features["rsi_crossed_up"]:
                return {"reason": "signal_reversal"}
        
        return None
    
    def _execute_entry(self, price: float, side: str, features: dict):
        """Execute entry order"""
        atr = features["atr"]
        current_bar = self._features.current_bar
        
        # Calculate SL/TP
        if side == "long":
            sl_price = price - (atr * self._cfg.risk.sl_atr_mult)
            tp_price = price + (atr * self._cfg.risk.tp_atr_mult)
        else:
            sl_price = price + (atr * self._cfg.risk.sl_atr_mult)
            tp_price = price - (atr * self._cfg.risk.tp_atr_mult)
        
        # Position size (simple fixed budget for now)
        size = (self._cfg.sizing.quote_budget or 100.0) / price
        
        self._position = {
            "side": side,
            "entry_price": price,
            "size": size,
            "entry_bar": current_bar,
            "sl_price": sl_price,
            "tp_price": tp_price
        }
        
        logger.info(f"ENTRY {side.upper()}: price={price:.2f}, sl={sl_price:.2f}, tp={tp_price:.2f}")
    
    def _execute_exit(self, price: float, reason: str):
        """Execute exit order"""
        side = self._position["side"]
        entry_price = self._position["entry_price"]
        size = self._position["size"]
        
        # Calculate PnL
        if side == "long":
            pnl = (price - entry_price) * size
        else:
            pnl = (entry_price - price) * size
        
        # Deduct fees
        fee = (entry_price + price) * size * (self._cfg.risk.fee_bps / 10000.0)
        net_pnl = pnl - fee
        
        self._total_pnl += net_pnl
        
        if net_pnl > 0:
            self._num_wins += 1
        else:
            self._num_losses += 1
        
        # Log trade
        self._trade_log.append({
            "timestamp": time.time(),
            "side": side,
            "entry_price": round(entry_price, 2),
            "exit_price": round(price, 2),
            "size": round(size, 6),
            "pnl": round(net_pnl, 2),
            "reason": reason
        })
        
        # Reset position
        self._last_exit_bar = self._features.current_bar
        self._position = {
            "side": None,
            "entry_price": 0.0,
            "size": 0.0,
            "entry_bar": 0,
            "sl_price": 0.0,
            "tp_price": 0.0
        }
        
        logger.info(f"EXIT {side.upper()}: price={price:.2f}, pnl={net_pnl:.2f}, reason={reason}")
    
    def _is_in_cooldown(self) -> bool:
        """Check if strategy is in cooldown period"""
        if self._cfg.cooldown_bars == 0:
            return False
        
        bars_since_exit = self._features.current_bar - self._last_exit_bar
        return bars_since_exit < self._cfg.cooldown_bars
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate"""
        total = self._num_wins + self._num_losses
        if total == 0:
            return 0.0
        return round((self._num_wins / total) * 100, 1)
    
    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        gross_profit = sum(t["pnl"] for t in self._trade_log if t["pnl"] > 0)
        gross_loss = abs(sum(t["pnl"] for t in self._trade_log if t["pnl"] < 0))
        
        if gross_loss == 0:
            return 0.0 if gross_profit == 0 else 999.0
        
        return round(gross_profit / gross_loss, 2)


