from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..infra import config_store

router = APIRouter()


@router.get("/config")
def get_config():
    return config_store.load()


@router.put("/config")
def update_config(patch: dict):
    try:
        cfg = config_store.load()
        cfg = config_store.deep_merge(cfg, patch)
        config_store.save(cfg)
        return {"ok": True, "config": cfg}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
