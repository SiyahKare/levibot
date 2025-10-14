from __future__ import annotations

import os
import socket
import threading
import time

import pytest
from uvicorn import Config, Server


def _free_port() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close(); return port

@pytest.fixture(scope="session")
def e2e_tmpdir(tmp_path_factory):
    p = tmp_path_factory.mktemp("e2e")
    # redirect logs -> tmp
    log_dir = p / "logs"
    data_dir = p / "data"
    log_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["LOG_DIR"] = str(log_dir)
    os.environ["DATA_DIR"] = str(data_dir)
    os.environ["PYTHONUNBUFFERED"] = "1"
    os.environ["TZ"] = "Europe/Istanbul"
    os.environ["ENV"] = "test"
    os.environ["AUTO_ROUTE_ENABLED"] = "true"
    os.environ["AUTO_ROUTE_DRY_RUN"] = "true"   # e2e'de fill tetiklenir ama paper emir logları güvenli
    os.environ["AUTO_ROUTE_MIN_CONF"] = "0.50"
    os.environ["CORS_ORIGINS"] = "http://localhost:5173"
    os.environ["RATE_LIMIT_WINDOW_SEC"] = "5"
    os.environ["RATE_LIMIT_MAX"] = "50"
    os.environ["API_KEYS"] = "test-e2e"
    # ensure model artifacts dir exists
    (p / "backend" / "artifacts").mkdir(parents=True, exist_ok=True)
    return p

@pytest.fixture(scope="session")
def base_url() -> str:
    port = _free_port()
    return f"http://127.0.0.1:{port}"

@pytest.fixture(scope="session", autouse=True)
def start_server(base_url, e2e_tmpdir):
    port = int(base_url.split(":")[-1])
    # Import app here to ensure ENV vars are set
    from backend.src.app.main import app
    
    config = Config(app=app, host="127.0.0.1", port=port, log_level="warning")
    server = Server(config=config)
    
    def run():
        server.run()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    
    # Wait for server to be ready
    import httpx
    for _ in range(50):
        try:
            httpx.get(f"{base_url}/healthz", timeout=0.5)
            break
        except:
            time.sleep(0.1)
    
    yield
    
    # Shutdown
    server.should_exit = True
