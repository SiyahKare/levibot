"""
Test Model Pack
Validates model selection, prediction, and logging functionality
"""

import os
import time

import requests

API = os.getenv("API_URL", "http://localhost:8000")


def test_models_list_and_select():
    """Test listing available models and selecting one."""
    print("📋 Testing model listing...")

    # List available models
    r = requests.get(f"{API}/ai/models")
    assert r.ok, f"Failed to list models: {r.status_code}"

    data = r.json()
    assert "models" in data, "Response missing 'models' field"
    assert "current" in data, "Response missing 'current' field"
    assert len(data["models"]) > 0, "No models available"

    print(f"✅ Found {len(data['models'])} models: {data['models']}")
    print(f"   Current model: {data['current']}")

    # Select first model
    model_name = data["models"][0]
    print(f"\n🎯 Testing model selection: {model_name}...")

    s = requests.post(f"{API}/ai/select", json={"name": model_name})
    assert s.ok, f"Failed to select model: {s.status_code}"

    select_data = s.json()
    assert select_data.get("ok"), f"Selection failed: {select_data.get('error')}"
    assert select_data.get("current") == model_name, "Model not updated"

    print(f"✅ Model selected: {model_name}")


def test_predict_and_log():
    """Test prediction generation and logging."""
    print("\n🔮 Testing prediction...")

    # Generate prediction
    r = requests.get(f"{API}/ai/predict", params={"symbol": "BTCUSDT", "h": "60s"})
    assert r.ok, f"Failed to predict: {r.status_code}"

    pred = r.json()
    assert "prob_up" in pred, "Prediction missing 'prob_up' field"
    assert "model" in pred, "Prediction missing 'model' field"
    assert "symbol" in pred, "Prediction missing 'symbol' field"

    prob_up = pred.get("prob_up", 0)
    assert 0 <= prob_up <= 1, f"Invalid prob_up value: {prob_up}"

    print(
        f"✅ Prediction: {pred['symbol']} prob_up={prob_up:.2%} model={pred['model']}"
    )

    # Wait for logging
    time.sleep(0.5)

    # Check prediction log
    print("\n📊 Testing prediction log...")

    l = requests.get(f"{API}/analytics/predictions/recent?limit=5")
    assert l.ok, f"Failed to fetch log: {l.status_code}"

    log_data = l.json()
    assert "items" in log_data, "Log missing 'items' field"

    if len(log_data["items"]) > 0:
        latest = log_data["items"][0]
        print(
            f"✅ Latest logged prediction: {latest.get('symbol')} @ {latest.get('model')}"
        )
    else:
        print("⚠️  No predictions in log yet")


def test_model_persistence():
    """Test that model selection persists."""
    print("\n💾 Testing model persistence...")

    # Get current models
    r1 = requests.get(f"{API}/ai/models")
    assert r1.ok
    models = r1.json()["models"]

    # Select second model (if available)
    if len(models) < 2:
        print("⚠️  Only one model available, skipping persistence test")
        return

    target_model = models[1]

    # Select model
    s = requests.post(f"{API}/ai/select", json={"name": target_model})
    assert s.ok

    # Verify selection
    r2 = requests.get(f"{API}/ai/models")
    assert r2.ok

    current = r2.json()["current"]
    assert (
        current == target_model
    ), f"Model not persisted: expected {target_model}, got {current}"

    print(f"✅ Model persisted: {current}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Model Pack Test Suite")
    print("=" * 60)

    try:
        test_models_list_and_select()
        test_predict_and_log()
        test_model_persistence()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        exit(1)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Unexpected error: {e}")
        print("=" * 60)
        exit(1)
