-- Trades Table Enrichment
-- Adds strategy, reason, and confidence columns for analytics

-- Add columns (idempotent)
ALTER TABLE trades ADD COLUMN IF NOT EXISTS strategy   TEXT;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS reason     TEXT;
ALTER TABLE trades ADD COLUMN IF NOT EXISTS confidence NUMERIC;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS ix_trades_ts        ON trades (ts DESC);
CREATE INDEX IF NOT EXISTS ix_trades_strategy  ON trades (strategy);

-- Comments
COMMENT ON COLUMN trades.strategy IS 'Strategy name that generated this trade (e.g., telegram_llm, manual)';
COMMENT ON COLUMN trades.reason IS 'AI-generated brief explanation for the trade';
COMMENT ON COLUMN trades.confidence IS 'Signal confidence score (0.0 to 1.0)';

