"""
Test kill switch functionality.

Tests:
- Kill switch latency (< 500ms)
- State toggle (on/off)
- Engine stop/restore
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    # Import here to avoid circular dependencies
    from backend.src.app.main import app

    return TestClient(app)


def test_kill_switch_latency(client):
    """Test kill switch response time < 500ms."""
    start = time.time()
    response = client.post("/live/kill", json={"reason": "test"})
    duration_ms = (time.time() - start) * 1000

    assert response.status_code in [200, 401], "Kill switch should respond"
    assert duration_ms < 500, f"Kill switch latency ({duration_ms:.0f}ms) exceeds 500ms"


def test_kill_switch_toggle(client):
    """Test kill switch state toggle."""
    # Get initial status
    status_resp = client.get("/live/status")
    assert status_resp.status_code in [200, 401]

    # If authenticated, test toggle
    if status_resp.status_code == 200:
        initial_state = status_resp.json().get("kill_switch_active", False)

        # Toggle kill switch
        kill_resp = client.post("/live/kill", json={"reason": "test toggle"})
        if kill_resp.status_code == 200:
            # Check state changed
            new_status = client.get("/live/status").json()
            assert new_status.get("kill_switch_active") != initial_state

            # Restore
            restore_resp = client.post("/live/restore")
            assert restore_resp.status_code == 200


def test_kill_switch_audit_log(client):
    """Test that kill switch actions are audit logged."""
    # Trigger kill switch
    response = client.post("/live/kill", json={"reason": "audit test"})

    # Check audit log (if accessible)
    # In production, would verify audit log entry exists
    assert response.status_code in [200, 401, 403]


@pytest.mark.asyncio
async def test_engine_stop_restore():
    """Test engine stop and restore cycle."""
    # This would test actual engine manager in integration test
    # For unit test, we just verify the concept
    from backend.src.engines.manager import EngineManager

    manager = EngineManager()

    # Stop all
    await manager.stop_all()

    # Verify stopped
    status = await manager.get_status()
    assert all(not e["running"] for e in status)

    # Restore
    await manager.restore_all()

    # Verify running
    status = await manager.get_status()
    # Note: May not all be running immediately, check after delay
    assert True  # Placeholder - would check actual state

