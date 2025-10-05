from __future__ import annotations

import os
import json
import datetime as dt
from pathlib import Path
from os import getenv
import zstandard as zstd
import boto3


BASE_DATA_DIR = Path(getenv("LEVI_DATA_DIR") or (Path(__file__).resolve().parents[2] / "data"))
LOG_ROOT = BASE_DATA_DIR / "logs"
S3_BUCKET = os.getenv("S3_LOG_BUCKET", "levibot-logs")


def compress_day(day: str) -> Path:
    day_dir = LOG_ROOT / day  # "YYYY-MM-DD"
    if not day_dir.exists():
        raise FileNotFoundError(f"no logs for {day}")
    out = (LOG_ROOT / f"{day}.zst")  # data/logs/2025-09-12.zst
    cctx = zstd.ZstdCompressor(level=10)
    with open(out, "wb") as f_out:
        with cctx.stream_writer(f_out) as compressor:
            for p in sorted(day_dir.glob("*.jsonl")):
                with open(p, "rb") as f_in:
                    for chunk in iter(lambda: f_in.read(1 << 20), b""):
                        compressor.write(chunk)
    return out


def upload_s3(zst_path: Path, day: str) -> str:
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
    key = f"{day}/{zst_path.name}"
    s3.upload_file(str(zst_path), S3_BUCKET, key, ExtraArgs={"ContentType": "application/zstd"})
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=f"{day}/manifest.json",
        Body=json.dumps({"date": day, "object": key}, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )
    return f"s3://{S3_BUCKET}/{key}"


def archive_day(day: str) -> str:
    zst = compress_day(day)
    url = upload_s3(zst, day)
    return url


def gc_local(retain_days: int = 30):
    cutoff = (dt.date.today() - dt.timedelta(days=retain_days)).isoformat()
    if not LOG_ROOT.exists():
        return
    for d in LOG_ROOT.iterdir():
        if d.is_dir() and d.name < cutoff:
            for p in d.glob("*"):
                try:
                    p.unlink()
                except Exception:
                    pass
            try:
                d.rmdir()
            except Exception:
                pass


