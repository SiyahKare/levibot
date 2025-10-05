from __future__ import annotations
import os, sys, gzip, shutil, time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple

try:
    import boto3  # type: ignore
except Exception as e:
    print("boto3 missing: pip install boto3", file=sys.stderr); raise

BASE = Path(__file__).resolve().parents[3] / "backend" / "data" / "logs"

def _env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise SystemExit(f"missing env: {name}")
    return v

def discover_days(keep_days: int) -> Tuple[List[Path], List[Path]]:
    """Return (archive_days, delete_days).
       archive_days: günün kendisi hariç son 'keep_days' içindeki *tamamlanan* günler
       delete_days: keep_days'den daha eski tüm günler
    """
    if not BASE.exists():
        return ([], [])
    days = sorted([p for p in BASE.iterdir() if p.is_dir()])
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cutoff = datetime.utcnow() - timedelta(days=keep_days)

    to_archive, to_delete = [], []
    for d in days:
        try:
            day_dt = datetime.strptime(d.name, "%Y-%m-%d")
        except Exception:
            continue
        if d.name == today:
            continue  # devam eden gün, skip
        if day_dt >= cutoff:
            to_archive.append(d)
        else:
            to_delete.append(d)
    return (to_archive, to_delete)

def compress_day(day_dir: Path) -> Path:
    """Concatenate all events-*.jsonl → events.jsonl.gz and return path."""
    target = day_dir.with_suffix(".jsonl.gz")  # e.g. 2025-10-05.jsonl.gz
    tmp = target.with_suffix(".tmp")
    with gzip.open(tmp, "wb") as gz:
        for fp in sorted(day_dir.glob("events-*.jsonl")):
            with open(fp, "rb") as f:
                shutil.copyfileobj(f, gz)
    tmp.rename(target)
    return target

def upload_s3(local_gz: Path, bucket: str, prefix: str) -> str:
    key = f"{prefix.rstrip('/')}/{local_gz.name}"
    s3 = boto3.client("s3",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL", None),
        aws_access_key_id=_env("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=_env("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "eu-central-1"),
    )
    # multipart upload otomatik: client.upload_file
    s3.upload_file(str(local_gz), bucket, key, ExtraArgs={"ContentType": "application/gzip"})
    return key

def remove_local(day_dir: Path, gz_file: Path) -> None:
    # güvenli sil: önce klasörü, sonra gz
    for fp in day_dir.glob("*"):
        try: fp.unlink()
        except: pass
    try: day_dir.rmdir()
    except: pass
    try: gz_file.unlink()  # gzip'i de siliyoruz (isteğe bağlı, S3'te var artık)
    except: pass

def prune_old(delete_days: List[Path]) -> None:
    for d in delete_days:
        for fp in d.glob("*"):
            try: fp.unlink()
            except: pass
        try: d.rmdir()
        except: pass

def main() -> int:
    bucket = _env("S3_LOG_BUCKET")
    prefix = os.getenv("S3_LOG_PREFIX", "levibot/logs")
    keep_days = int(os.getenv("ARCHIVE_KEEP_DAYS", "7"))
    dry_run = os.getenv("ARCHIVE_DRY_RUN", "false").lower() == "true"

    to_archive, to_delete = discover_days(keep_days)
    print(f"[archiver] keep_days={keep_days} archive={len(to_archive)} delete={len(to_delete)} dry_run={dry_run}")

    for day_dir in to_archive:
        print(f"[archiver] compressing {day_dir} ...")
        gz = compress_day(day_dir)
        print(f"[archiver] uploading {gz.name} to s3://{bucket}/{prefix} ...")
        if not dry_run:
            key = upload_s3(gz, bucket, prefix)
            print(f"[archiver] uploaded s3://{bucket}/{key}")
            remove_local(day_dir, gz)
        else:
            print(f"[archiver] DRY_RUN — skip upload/remove {gz}")

    if not dry_run and to_delete:
        print(f"[archiver] pruning {len(to_delete)} old day(s)")
        prune_old(to_delete)
    return 0

if __name__ == "__main__":
    sys.exit(main())
