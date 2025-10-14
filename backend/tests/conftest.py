from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def global_tmp_dirs(tmp_path_factory):
    base = tmp_path_factory.mktemp("session_paths")
    log_dir = base / "logs"
    data_dir = base / "data"
    log_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    orig_log = os.environ.get("LOG_DIR")
    orig_data = os.environ.get("DATA_DIR")

    os.environ["LOG_DIR"] = str(log_dir)
    os.environ["DATA_DIR"] = str(data_dir)

    yield

    if orig_log is not None:
        os.environ["LOG_DIR"] = orig_log
    else:
        os.environ.pop("LOG_DIR", None)

    if orig_data is not None:
        os.environ["DATA_DIR"] = orig_data
    else:
        os.environ.pop("DATA_DIR", None)
