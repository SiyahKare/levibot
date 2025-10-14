"""
Realtime Health Pytest Suite

Quick smoke tests for critical endpoints.
"""

import os

import pytest
import requests
from requests.exceptions import RequestException

API = os.getenv("API_URL", "http://localhost:8000")


def _http_get(path: str, timeout: int = 3, stream: bool = False):
    """Helper that skips tests when backend is unreachable."""
    url = f"{API}{path}"
    try:
        return requests.get(url, timeout=timeout, stream=stream)
    except RequestException as exc:  # pragma: no cover - defensive guard
        pytest.skip(f"Backend not reachable at {url}: {exc}")


def test_healthz():
    """Test /healthz endpoint."""
    r = _http_get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True


def test_metrics():
    """Test /metrics endpoint."""
    r = _http_get("/metrics")
    assert r.status_code == 200
    assert "levibot_" in r.text


def test_paper_portfolio():
    """Test paper portfolio endpoint."""
    r = _http_get("/paper/portfolio")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert "total_equity" in data


def test_analytics_stats():
    """Test analytics endpoint."""
    r = _http_get("/analytics/stats?days=1", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "event_types" in data


@pytest.mark.skipif(
    not os.getenv("TEST_SSE"), reason="SSE test requires sseclient-py and may timeout"
)
def test_sse_stream():
    """Test SSE stream (optional, needs sseclient-py)."""
    try:
        import sseclient  # noqa: F401
    except ImportError:
        pytest.skip("sseclient-py not installed")

    r = _http_get("/stream/ticks", timeout=10, stream=True)
    assert r.status_code == 200

    from sseclient import SSEClient

    client = SSEClient(r)
    events = []
    import time

    start = time.time()
    for event in client.events():
        events.append(event)
        if len(events) >= 1 or time.time() - start > 5:
            break

    # At least connection established
    assert r.status_code == 200
