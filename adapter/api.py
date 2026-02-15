from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
import yaml
from fastapi import FastAPI, Header, HTTPException

from adapter.chat_service import get_chat_service
from core.executor import RPAExecutor
from core.registry import RPA_REGISTRY
from core.schema import ChatSendRequest, EmbeddingTestRequest, RunRequest

BASE_DIR = Path(__file__).resolve().parent.parent


def load_config() -> dict[str, Any]:
    with (BASE_DIR / "config.yaml").open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


app = FastAPI(title="RPA Agent API")


def auth(api_key: str | None) -> None:
    config = load_config()
    if api_key != config["api"]["api_key"]:
        raise HTTPException(status_code=403, detail="API Key 錯誤")


def _default_chat_session() -> str:
    config = load_config()
    return config.get("chat", {}).get("default_session", "dash:default")


@app.post("/api/rpa/run")
def run_rpa(req: RunRequest, api_key: str | None = Header(default=None, alias="api_key")):
    auth(api_key)
    return RPAExecutor.run(req.rpa_name, req.params)


@app.get("/api/rpa/list")
def list_rpa(api_key: str | None = Header(default=None, alias="api_key")):
    auth(api_key)
    data = [{"name": name, "desc": item["desc"]} for name, item in RPA_REGISTRY.items()]
    return {"code": 200, "data": data}


@app.post("/api/chat/send")
def chat_send(req: ChatSendRequest, api_key: str | None = Header(default=None, alias="api_key")):
    auth(api_key)
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message 不可為空")

    session_key = req.session_key or _default_chat_session()
    service = get_chat_service(load_config)
    run_id = service.submit(message, session_key)
    return {"code": 200, "run_id": run_id, "status": "queued", "session_key": session_key}


@app.get("/api/chat/status/{run_id}")
def chat_status(run_id: str, api_key: str | None = Header(default=None, alias="api_key")):
    auth(api_key)
    service = get_chat_service(load_config)
    data = service.get_status(run_id)
    return {"code": 200, "data": data}


@app.get("/api/chat/history")
def chat_history(session_key: str | None = None, limit: int = 30, api_key: str | None = Header(default=None, alias="api_key")):
    auth(api_key)
    service = get_chat_service(load_config)
    key = session_key or _default_chat_session()
    rows = service.get_history(key, max(1, min(limit, 200)))
    return {"code": 200, "data": rows, "session_key": key}


@app.post("/api/embedding/test")
def embedding_test(req: EmbeddingTestRequest, api_key: str | None = Header(default=None, alias="api_key")):
    auth(api_key)
    config = load_config()
    emb = config.get("embedding", {})

    if not emb.get("enabled", False):
        raise HTTPException(status_code=400, detail="embedding 未啟用")

    base_url = str(emb.get("base_url") or "").rstrip("/")
    model = emb.get("model")
    if not base_url or not model:
        raise HTTPException(status_code=400, detail="embedding base_url/model 缺失")

    endpoint = f"{base_url}/embeddings" if base_url.endswith("/v1") else f"{base_url}/v1/embeddings"

    headers: dict[str, str] = {}
    cfg_headers = emb.get("headers", {})
    if isinstance(cfg_headers, dict):
        headers.update({str(k): str(v) for k, v in cfg_headers.items()})

    emb_key = emb.get("api_key")
    if emb_key and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {emb_key}"

    payload = {
        "model": model,
        "input": req.input_text,
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        body = response.json()

        vector = None
        if isinstance(body, dict) and isinstance(body.get("data"), list) and body["data"]:
            vector = body["data"][0].get("embedding")
        dimension = len(vector) if isinstance(vector, list) else None

        return {
            "code": 200,
            "status": "ok",
            "endpoint": endpoint,
            "model": model,
            "dimension": dimension,
            "usage": body.get("usage") if isinstance(body, dict) else None,
        }
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"embedding 連通測試失敗: {exc}")
