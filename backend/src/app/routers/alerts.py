from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

from ...alerts.channels import deliver_alert_via, route_targets

router = APIRouter(prefix="/alerts", tags=["alerts"])


class TriggerAlertRequest(BaseModel):
    title: str
    summary: str
    severity: str = "info"  # info | low | medium | high | critical
    source: str = "manual"
    labels: Optional[Dict[str, str]] = None
    url: Optional[str] = None


class TriggerAlertResponse(BaseModel):
    status: str
    targets: List[str]


@router.post("/trigger", response_model=TriggerAlertResponse)
async def trigger_alert(req: TriggerAlertRequest):
    """Manually trigger an alert (for testing/demo)."""
    from ...app.main import WEBHOOK_QUEUE
    
    if not WEBHOOK_QUEUE:
        raise HTTPException(status_code=503, detail="webhook queue not available")
    
    alert = {
        "title": req.title,
        "summary": req.summary,
        "severity": req.severity,
        "source": req.source,
        "labels": req.labels or {},
        "url": req.url,
    }
    
    targets = route_targets()
    if not targets:
        raise HTTPException(status_code=400, detail="no alert targets configured")
    
    for target in targets:
        deliver_alert_via(target, alert, WEBHOOK_QUEUE)
    
    # Log to JSONL
    _log_alert(alert)
    
    return TriggerAlertResponse(status="queued", targets=targets)


@router.get("/history")
async def get_alert_history(
    limit: int = 50,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    days: int = 7
):
    """Get alert history from JSONL logs."""
    log_dir = Path(os.getenv("ALERT_LOG_DIR", "backend/data/alerts"))
    if not log_dir.exists():
        return {"alerts": []}
    
    # Collect alerts from last N days
    alerts = []
    today = datetime.utcnow().date()
    for i in range(days):
        day = today - timedelta(days=i)
        day_dir = log_dir / day.strftime("%Y-%m-%d")
        if not day_dir.exists():
            continue
        
        for log_file in sorted(day_dir.glob("alerts*.jsonl")):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            alert = json.loads(line.strip())
                            # Apply filters
                            if severity and alert.get("severity") != severity:
                                continue
                            if source and alert.get("source") != source:
                                continue
                            alerts.append(alert)
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue
    
    # Sort by timestamp (newest first) and limit
    alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    limited = alerts[:limit]
    return {"alerts": limited, "total": len(limited)}


def _log_alert(alert: Dict[str, Any]) -> None:
    """Log alert to JSONL file."""
    log_dir = Path(os.getenv("ALERT_LOG_DIR", "backend/data/alerts"))
    today = datetime.utcnow().date()
    day_dir = log_dir / today.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = day_dir / "alerts.jsonl"
    record = {
        **alert,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Silent fail for logging
