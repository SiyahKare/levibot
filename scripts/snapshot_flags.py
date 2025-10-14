#!/usr/bin/env python3
"""
Config Snapshot Tool
Captures current runtime flags for deployment auditing
"""
import json
import os
import time
from pathlib import Path

import requests


def main():
    """Take snapshot of current runtime flags."""
    # Configuration
    api_url = os.getenv("API_URL", "http://localhost:8000")
    snap_dir = Path(os.getenv("SNAP_DIR", "ops/config-snapshots"))
    
    # Ensure output directory exists
    snap_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📸 Taking config snapshot from {api_url}")
    
    try:
        # Fetch current flags
        response = requests.get(f"{api_url}/admin/flags", timeout=5)
        response.raise_for_status()
        
        flags_data = response.json()
        
        # Create snapshot
        snapshot = {
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "flags": flags_data.get("flags", {}),
            "source": api_url
        }
        
        # Save to file
        filename = f"flags_{int(snapshot['timestamp'])}.json"
        filepath = snap_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(snapshot, f, indent=2)
        
        print(f"✅ Snapshot saved: {filepath}")
        print(f"   Timestamp: {snapshot['iso_timestamp']}")
        print(f"   Flags captured: {len(snapshot['flags'])}")
        
        # Keep only last 30 snapshots
        cleanup_old_snapshots(snap_dir, keep=30)
        
        return 0
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch flags: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 2


def cleanup_old_snapshots(snap_dir: Path, keep: int = 30):
    """Remove old snapshots, keeping only the most recent."""
    snapshots = sorted(snap_dir.glob("flags_*.json"), reverse=True)
    
    if len(snapshots) > keep:
        for old_snap in snapshots[keep:]:
            old_snap.unlink()
            print(f"🗑️  Removed old snapshot: {old_snap.name}")


if __name__ == "__main__":
    exit(main())

