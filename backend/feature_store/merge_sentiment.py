"""
Sentiment Merge - Score Telegram messages with AI and merge to feature store
Input: backend/data/logs/telethon/*.jsonl
Output: data/sentiment/telegram_impact.parquet
"""
import glob
import json
from pathlib import Path

try:
    import polars as pl
except ImportError:
    print("Warning: polars not installed, skipping")
    pl = None

# Import AI scoring (if available)
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ai.openai_client import score_headlines
except ImportError:
    print("Warning: OpenAI client not available, using fallback")
    def score_headlines(headlines):
        return [{"impact": 0.0, "confidence": 0.5} for _ in headlines]


def load_lines():
    """Load all lines from Telethon JSONL logs."""
    files = glob.glob("backend/data/logs/telethon/*.jsonl")
    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        yield json.loads(line)
                    except Exception:
                        pass
        except Exception:
            pass


def run():
    """Score Telegram messages and save to parquet."""
    if not pl:
        print("Polars not installed, skipping sentiment merge")
        return
    
    print("[sentiment] Loading Telegram messages...")
    rows = []
    buf = []
    buf_docs = []
    
    for doc in load_lines():
        # Skip errors
        if "error" in doc:
            continue
        
        txt = (doc.get("text") or "").strip()
        if not txt:
            continue
        
        buf.append(txt)
        buf_docs.append(doc)
        
        # Batch score every 8 messages
        if len(buf) >= 8:
            print(f"[sentiment] Scoring {len(buf)} messages...")
            scored = score_headlines(buf)
            
            for d, sc in zip(buf_docs, scored):
                rows.append({
                    "ts": d.get("date"),
                    "chat": d.get("chat"),
                    "hash": d.get("hash", ""),
                    "text": d.get("text", "")[:200],  # First 200 chars
                    "impact": sc.get("impact", 0.0),
                    "confidence": sc.get("confidence", 0.5),
                    "asset": sc.get("asset", "MKT"),
                    "event_type": sc.get("event_type", "unknown"),
                })
            
            buf = []
            buf_docs = []
    
    # Score remaining messages
    if buf:
        print(f"[sentiment] Scoring remaining {len(buf)} messages...")
        scored = score_headlines(buf)
        for d, sc in zip(buf_docs, scored):
            rows.append({
                "ts": d.get("date"),
                "chat": d.get("chat"),
                "hash": d.get("hash", ""),
                "text": d.get("text", "")[:200],
                "impact": sc.get("impact", 0.0),
                "confidence": sc.get("confidence", 0.5),
                "asset": sc.get("asset", "MKT"),
                "event_type": sc.get("event_type", "unknown"),
            })
    
    if not rows:
        print("[sentiment] No messages to score")
        return
    
    # Save to parquet
    df = pl.DataFrame(rows)
    out_dir = Path("backend/data/sentiment")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "telegram_impact.parquet"
    
    df.write_parquet(out_path)
    print(f"[sentiment] Wrote {len(df)} scored messages to {out_path}")
    
    # Print summary
    print("\n[sentiment] Summary:")
    print(f"  Total messages: {len(df)}")
    print(f"  Avg impact: {df['impact'].mean():.3f}")
    print(f"  Avg confidence: {df['confidence'].mean():.3f}")
    print(f"  Top assets: {df.group_by('asset').count().sort('count', descending=True).head(5)}")


if __name__ == "__main__":
    run()

