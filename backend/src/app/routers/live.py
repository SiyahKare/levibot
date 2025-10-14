"""Live trading control: kill switch, mode toggle, status."""

from fastapi import APIRouter

router = APIRouter(prefix="/live", tags=["live"])

# Global kill switch state (in production, use shared state manager)
_kill_switch_state = {"engaged": False, "reason": ""}


@router.post("/kill")
async def toggle_kill_switch(on: bool, reason: str = "manual"):
    """
    Engage or disengage kill switch.

    Args:
        on: True to engage, False to disengage
        reason: Reason for engagement

    Returns:
        Current kill switch status
    """
    global _kill_switch_state
    _kill_switch_state["engaged"] = on
    _kill_switch_state["reason"] = reason if on else "disengaged"

    return {
        "kill_switch": _kill_switch_state["engaged"],
        "reason": _kill_switch_state["reason"],
        "message": "Kill switch engaged" if on else "Kill switch disengaged",
    }


@router.get("/status")
async def live_status():
    """
    Get live trading status.

    Returns:
        Status dict with kill_switch_active (bool) for frontend compatibility.
    """
    return {
        "kill_switch_active": _kill_switch_state["engaged"],
        "reason": _kill_switch_state["reason"],
        "mode": "paper",  # TODO: Load from config
        "active": not _kill_switch_state["engaged"],
    }

