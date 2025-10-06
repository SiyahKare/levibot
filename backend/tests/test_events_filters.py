"""
Test suite for /events endpoint smart filters (PR-40)
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.app.main import app

client = TestClient(app)


def test_events_no_filters():
    """Test /events without any filters - should return recent events"""
    response = client.get("/events?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10


def test_events_filter_event_type():
    """Test event_type filter (CSV list)"""
    response = client.get("/events?event_type=SIGNAL_SCORED&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All returned events should be SIGNAL_SCORED
    for event in data:
        assert event.get("event_type") == "SIGNAL_SCORED"


def test_events_filter_event_type_csv():
    """Test event_type filter with multiple types (CSV)"""
    response = client.get("/events?event_type=SIGNAL_SCORED,POSITION_CLOSED&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All returned events should be one of the specified types
    allowed_types = {"SIGNAL_SCORED", "POSITION_CLOSED"}
    for event in data:
        assert event.get("event_type") in allowed_types


def test_events_filter_symbol():
    """Test symbol filter (exact match)"""
    response = client.get("/events?symbol=BTCUSDT&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All returned events should have symbol=BTCUSDT
    for event in data:
        assert event.get("symbol") == "BTCUSDT"


def test_events_filter_trace_id():
    """Test trace_id filter (exact match)"""
    # First, get an event with a trace_id
    response = client.get("/events?limit=100")
    assert response.status_code == 200
    data = response.json()
    
    # Find an event with a trace_id
    test_trace_id = None
    for event in data:
        if event.get("trace_id"):
            test_trace_id = event["trace_id"]
            break
    
    if test_trace_id:
        # Now filter by that trace_id
        response = client.get(f"/events?trace_id={test_trace_id}&limit=50")
        assert response.status_code == 200
        filtered_data = response.json()
        assert isinstance(filtered_data, list)
        
        # All returned events should have the same trace_id
        for event in filtered_data:
            assert event.get("trace_id") == test_trace_id


def test_events_filter_since_iso():
    """Test since_iso filter (date range)"""
    # Test with a recent date
    response = client.get("/events?since_iso=2025-10-06T00:00:00Z&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All returned events should have timestamp >= since
    for event in data:
        ts = event.get("ts", "")
        assert ts >= "2025-10-06T00:00:00Z"


def test_events_filter_q_text_search():
    """Test q parameter (full-text search in payload)"""
    response = client.get("/events?q=confidence&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # Events should contain "confidence" in their content
    # (event_type, symbol, trace_id, or payload)
    import json
    for event in data:
        combined = (
            event.get("event_type", "") + " " +
            str(event.get("symbol", "")) + " " +
            str(event.get("trace_id", "")) + " " +
            json.dumps(event.get("payload", {}), ensure_ascii=False)
        ).lower()
        assert "confidence" in combined


def test_events_filter_combined():
    """Test multiple filters combined"""
    response = client.get(
        "/events?event_type=SIGNAL_SCORED&symbol=BTCUSDT&limit=50"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # All events should match both filters
    for event in data:
        assert event.get("event_type") == "SIGNAL_SCORED"
        assert event.get("symbol") == "BTCUSDT"


def test_events_limit_boundary():
    """Test limit parameter boundary (max 1000)"""
    # Should accept limit=1000
    response = client.get("/events?limit=1000")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1000
    
    # Should reject limit > 1000
    response = client.get("/events?limit=2000")
    assert response.status_code == 422  # Validation error


def test_events_days_boundary():
    """Test days parameter boundary (1-7)"""
    # Should accept days=7
    response = client.get("/events?days=7&limit=10")
    assert response.status_code == 200
    
    # Should reject days=0
    response = client.get("/events?days=0&limit=10")
    assert response.status_code == 422  # Validation error
    
    # Should reject days > 7
    response = client.get("/events?days=10&limit=10")
    assert response.status_code == 422  # Validation error


def test_events_jsonl_format():
    """Test JSONL format output"""
    response = client.get("/events?format=jsonl&limit=10")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-ndjson"
    
    # Should be valid JSONL (one JSON object per line)
    lines = response.text.strip().split("\n")
    import json
    for line in lines:
        if line:  # Skip empty lines
            json.loads(line)  # Should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

