"""
AI-Powered Trading Engine

Uses machine learning to predict price movements and make intelligent trading decisions.
Combines technical analysis, ML predictions, and risk management.
"""
from collections import deque
from datetime import datetime

from ..exec.paper_portfolio import get_paper_portfolio
from ..infra.logger import log_event
from ..infra.price_cache import get_price


class PriceHistory:
    """Maintains rolling price history for technical analysis."""

    def __init__(self, max_len: int = 100):
        self.prices: dict[str, deque[tuple[float, float]]] = {}  # symbol -> [(timestamp, price)]
        self.max_len = max_len

    def add(self, symbol: str, price: float) -> None:
        """Add price to history."""
        if symbol not in self.prices:
            self.prices[symbol] = deque(maxlen=self.max_len)

        timestamp = datetime.now().timestamp()
        self.prices[symbol].append((timestamp, price))

    def get_returns(self, symbol: str, periods: list[int] = [1, 5, 10]) -> dict[str, float]:
        """Calculate returns over different periods."""
        if symbol not in self.prices or len(self.prices[symbol]) < max(periods) + 1:
            return {f"ret_{p}": 0.0 for p in periods}

        prices_list = list(self.prices[symbol])
        current = prices_list[-1][1]

        returns = {}
        for period in periods:
            if len(prices_list) > period:
                past = prices_list[-(period + 1)][1]
                returns[f"ret_{period}"] = (current - past) / past if past > 0 else 0.0
            else:
                returns[f"ret_{period}"] = 0.0

        return returns

    def get_volatility(self, symbol: str, period: int = 20) -> float:
        """Calculate price volatility (standard deviation of returns)."""
        if symbol not in self.prices or len(self.prices[symbol]) < period:
            return 0.0

        prices_list = [p[1] for p in list(self.prices[symbol])[-period:]]
        returns = [(prices_list[i] - prices_list[i - 1]) / prices_list[i - 1] for i in range(1, len(prices_list))]

        if not returns:
            return 0.0

        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        return variance**0.5

    def get_ma(self, symbol: str, period: int = 20) -> float | None:
        """Calculate moving average."""
        if symbol not in self.prices or len(self.prices[symbol]) < period:
            return None

        prices_list = [p[1] for p in list(self.prices[symbol])[-period:]]
        return sum(prices_list) / len(prices_list)

    def get_rsi(self, symbol: str, period: int = 14) -> float | None:
        """Calculate RSI indicator."""
        if symbol not in self.prices or len(self.prices[symbol]) < period + 1:
            return None

        prices_list = [p[1] for p in list(self.prices[symbol])[-(period + 1) :]]

        gains = []
        losses = []
        for i in range(1, len(prices_list)):
            change = prices_list[i] - prices_list[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if not gains or sum(losses) == 0:
            return 50.0

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class AITradingEngine:
    """
    AI-powered trading engine that uses ML predictions and technical analysis
    to make intelligent trading decisions.
    """

    def __init__(self):
        self.enabled = False
        self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
        self.history = PriceHistory(max_len=100)

        # Risk management
        self.max_positions = 3
        self.min_confidence = 0.65  # Minimum ML confidence to trade
        self.min_notional = 50
        self.max_notional = 150
        self.stop_loss_pct = 0.03  # 3% stop loss
        self.take_profit_pct = 0.05  # 5% take profit

        # Trading state
        self.cycle_count = 0
        self.trades_today = 0

    def update_prices(self) -> None:
        """Update price history for all tracked symbols."""
        for symbol in self.symbols:
            price = get_price(symbol)
            if price:
                self.history.add(symbol, price)

    def calculate_ml_score(self, symbol: str) -> float:
        """
        Get ML prediction from trained model with fallback to heuristics.
        Returns probability of upward movement (0-1).
        """
        try:
            from pathlib import Path

            import httpx
            
            # Check for kill switch
            kill_file = Path("backend/data/ml_kill_switch.flag")
            if kill_file.exists():
                return 0.5  # Neutral when kill switch is on
            
            # Call ML prediction API (internal, non-blocking)
            response = httpx.get(
                "http://127.0.0.1:8000/ml/predict",
                params={"symbol": symbol},
                timeout=2.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                # Use calibrated probability
                return data.get("p_up", 0.5)
        
        except Exception:
            pass
        
        # Fallback to heuristic scoring if ML API unavailable
        return self._fallback_score(symbol)
    
    def _fallback_score(self, symbol: str) -> float:
        """
        Fallback heuristic scoring when ML API is unavailable.
        
        Uses multiple signals:
        - Short-term momentum
        - Medium-term trend
        - Volatility regime
        - RSI overbought/oversold
        """
        returns = self.history.get_returns(symbol, periods=[1, 5, 10])
        volatility = self.history.get_volatility(symbol, period=20)
        ma_20 = self.history.get_ma(symbol, period=20)
        rsi = self.history.get_rsi(symbol, period=14)

        if not ma_20 or not rsi:
            return 0.5  # Neutral if not enough data

        # Get current price
        current_price = get_price(symbol)
        if not current_price:
            return 0.5

        # Feature engineering
        score = 0.5  # Start neutral

        # 1. Momentum signals (40% weight)
        if returns["ret_1"] > 0.001:  # Short-term up
            score += 0.10
        if returns["ret_5"] > 0.005:  # Medium-term up
            score += 0.15
        if returns["ret_10"] > 0.010:  # Long-term up
            score += 0.15

        # 2. Trend relative to MA (25% weight)
        ma_distance = (current_price - ma_20) / ma_20
        if ma_distance > 0.02:  # Price above MA
            score += 0.15
        elif ma_distance > 0:
            score += 0.10

        # 3. RSI signals (20% weight)
        if 30 < rsi < 70:  # Neutral zone
            score += 0.05
        elif rsi < 30:  # Oversold - buy signal
            score += 0.15
        elif rsi > 70:  # Overbought - avoid
            score -= 0.10

        # 4. Volatility regime (15% weight)
        if 0.01 < volatility < 0.03:  # Optimal volatility
            score += 0.10
        elif volatility > 0.05:  # Too volatile - risky
            score -= 0.05

        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))

    def should_buy(self, symbol: str) -> tuple[bool, float, dict]:
        """
        Decide whether to buy a symbol.
        Returns: (should_buy, confidence, reasoning)
        """
        ml_score = self.calculate_ml_score(symbol)

        reasoning = {
            "ml_score": ml_score,
            "returns": self.history.get_returns(symbol),
            "volatility": self.history.get_volatility(symbol),
            "rsi": self.history.get_rsi(symbol),
        }

        # Decision threshold
        should_buy = ml_score >= self.min_confidence

        return should_buy, ml_score, reasoning

    def should_sell(self, symbol: str, entry_price: float, current_price: float) -> tuple[bool, str]:
        """
        Decide whether to sell a position.
        Returns: (should_sell, reason)
        """
        # Calculate P&L
        pnl_pct = (current_price - entry_price) / entry_price

        # Stop loss
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"STOP_LOSS ({pnl_pct:.2%})"

        # Take profit
        if pnl_pct >= self.take_profit_pct:
            return True, f"TAKE_PROFIT ({pnl_pct:.2%})"

        # ML-based exit
        ml_score = self.calculate_ml_score(symbol)

        # Strong sell signal
        if ml_score < 0.40:
            return True, f"ML_SELL_SIGNAL (score={ml_score:.2f})"

        return False, "HOLD"

    def execute_buy(self, symbol: str, confidence: float, reasoning: dict) -> bool:
        """Execute a buy trade."""
        try:
            portfolio = get_paper_portfolio()
            price = get_price(symbol)

            if not price:
                print(f"⚠️  Could not get price for {symbol}")
                return False

            # Dynamic position sizing based on confidence
            base_notional = (self.min_notional + self.max_notional) / 2
            confidence_multiplier = 0.7 + (confidence - self.min_confidence) * 2  # 0.7 to 1.7x
            notional = min(self.max_notional, base_notional * confidence_multiplier)

            qty = notional / price

            success = portfolio.open_position(symbol, "long", qty, price, notional)

            if success:
                self.trades_today += 1
                log_event(
                    "AI_TRADE_EXECUTED",
                    {
                        "symbol": symbol,
                        "side": "BUY",
                        "price": price,
                        "qty": qty,
                        "notional": notional,
                        "confidence": confidence,
                        "reasoning": reasoning,
                    },
                    symbol=symbol,
                )
                print(
                    f"🤖 AI-Trade: BUY {symbol} ${notional:.0f} @ ${price:.2f} | Confidence: {confidence:.2%}"
                )
                return True
            else:
                print(f"❌ Insufficient balance for {symbol}")
                return False

        except Exception as e:
            print(f"⚠️  Buy error for {symbol}: {e}")
            return False

    def execute_sell(self, symbol: str, reason: str) -> bool:
        """Execute a sell trade."""
        try:
            portfolio = get_paper_portfolio()
            price = get_price(symbol)

            if not price:
                print(f"⚠️  Could not get price for {symbol}")
                return False

            trade = portfolio.close_position(symbol, price)

            if trade:
                self.trades_today += 1
                log_event(
                    "AI_TRADE_CLOSED",
                    {
                        "symbol": symbol,
                        "side": "SELL",
                        "price": price,
                        "pnl_usd": trade.pnl_usd,
                        "pnl_pct": trade.pnl_pct,
                        "reason": reason,
                        "duration_sec": trade.duration_sec,
                    },
                    symbol=symbol,
                )
                pnl_emoji = "🟢" if trade.pnl_usd >= 0 else "🔴"
                print(
                    f"🤖 AI-Close: SELL {symbol} @ ${price:.2f} | {pnl_emoji} PnL: ${trade.pnl_usd:.2f} ({trade.pnl_pct:.2%}) | {reason}"
                )
                return True
            else:
                print(f"❌ No position to close for {symbol}")
                return False

        except Exception as e:
            print(f"⚠️  Sell error for {symbol}: {e}")
            return False

    def run_cycle(self) -> None:
        """Run one AI trading cycle."""
        if not self.enabled:
            return

        self.cycle_count += 1

        try:
            # Update price history
            self.update_prices()

            portfolio = get_paper_portfolio()
            open_positions = portfolio.get_positions()

            print(f"\n⚡ AI Trading Cycle #{self.cycle_count} [{datetime.now().strftime('%H:%M:%S')}]")
            print(f"   Open Positions: {len(open_positions)} | Trades Today: {self.trades_today}")

            # 1. Check existing positions for exit signals
            for position in open_positions:
                current_price = get_price(position.symbol)
                if not current_price:
                    continue

                should_sell, reason = self.should_sell(position.symbol, position.entry_price, current_price)

                if should_sell:
                    self.execute_sell(position.symbol, reason)

            # 2. Look for new entry opportunities
            if len(open_positions) < self.max_positions:
                # Evaluate all symbols and rank by confidence
                opportunities = []

                for symbol in self.symbols:
                    # Skip if already have position
                    if any(p.symbol == symbol for p in open_positions):
                        continue

                    should_buy, confidence, reasoning = self.should_buy(symbol)

                    if should_buy:
                        opportunities.append((symbol, confidence, reasoning))

                # Sort by confidence (best first)
                opportunities.sort(key=lambda x: x[1], reverse=True)

                # Take top opportunity
                if opportunities:
                    symbol, confidence, reasoning = opportunities[0]
                    print(f"   🎯 Best Opportunity: {symbol} (confidence: {confidence:.2%})")
                    self.execute_buy(symbol, confidence, reasoning)
                else:
                    print("   💤 No opportunities above confidence threshold")
            else:
                print("   ⏸️  Max positions reached")

        except Exception as e:
            print(f"⚠️  AI Trading cycle error: {e}")
            log_event("ERROR", {"scope": "ai_trading_cycle", "err": str(e)})


# Global instance
_AI_ENGINE = None


def get_ai_engine() -> AITradingEngine:
    """Get or create global AI trading engine."""
    global _AI_ENGINE
    if _AI_ENGINE is None:
        _AI_ENGINE = AITradingEngine()
    return _AI_ENGINE

