from __future__ import annotations

import asyncio
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from nanobot_bridge.config_mapper import map_config_to_nanobot_runtime
from nanobot_tool import register_rpa_tool

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_NANOBOT_ROOT = BASE_DIR / "nanobot"

if LOCAL_NANOBOT_ROOT.exists() and str(LOCAL_NANOBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_NANOBOT_ROOT))


class ChatService:
    def __init__(self, config_loader):
        self._config_loader = config_loader
        self._agent = None
        self._agent_lock = threading.Lock()
        self._runs: dict[str, dict[str, Any]] = {}
        self._runs_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2)

    def _build_agent(self):
        from nanobot.agent.loop import AgentLoop
        from nanobot.bus.queue import MessageBus
        from nanobot.providers.litellm_provider import LiteLLMProvider

        config = self._config_loader()
        runtime = map_config_to_nanobot_runtime(config)
        provider_cfg = runtime.provider

        provider = LiteLLMProvider(
            api_key=provider_cfg.api_key,
            api_base=provider_cfg.api_base,
            default_model=provider_cfg.default_model,
            extra_headers=provider_cfg.extra_headers,
            provider_name=provider_cfg.provider_name,
        )

        bus = MessageBus()
        agent = AgentLoop(
            bus=bus,
            provider=provider,
            workspace=BASE_DIR,
            model=provider.get_default_model(),
            max_iterations=runtime.agent.max_iterations,
            memory_window=runtime.agent.memory_window,
            restrict_to_workspace=runtime.agent.restrict_to_workspace,
        )
        register_rpa_tool(agent.tools)
        return agent

    def _get_agent(self):
        with self._agent_lock:
            if self._agent is None:
                self._agent = self._build_agent()
            return self._agent

    def submit(self, message: str, session_key: str) -> str:
        run_id = uuid.uuid4().hex
        now = time.time()
        with self._runs_lock:
            self._runs[run_id] = {
                "run_id": run_id,
                "status": "queued",
                "session_key": session_key,
                "message": message,
                "result": None,
                "error": None,
                "created_at": now,
                "updated_at": now,
            }
        self._executor.submit(self._execute_run, run_id, message, session_key)
        return run_id

    def _execute_run(self, run_id: str, message: str, session_key: str) -> None:
        with self._runs_lock:
            if run_id in self._runs:
                self._runs[run_id]["status"] = "running"
                self._runs[run_id]["updated_at"] = time.time()

        try:
            agent = self._get_agent()
            result = asyncio.run(agent.process_direct(message, session_key=session_key))
            with self._runs_lock:
                if run_id in self._runs:
                    self._runs[run_id]["status"] = "final"
                    self._runs[run_id]["result"] = result
                    self._runs[run_id]["updated_at"] = time.time()
        except Exception as exc:
            with self._runs_lock:
                if run_id in self._runs:
                    self._runs[run_id]["status"] = "error"
                    self._runs[run_id]["error"] = str(exc)
                    self._runs[run_id]["updated_at"] = time.time()

    def get_status(self, run_id: str) -> dict[str, Any]:
        with self._runs_lock:
            data = self._runs.get(run_id)
            if not data:
                return {"run_id": run_id, "status": "not_found"}
            return dict(data)

    def get_history(self, session_key: str, limit: int = 30) -> list[dict[str, Any]]:
        agent = self._get_agent()
        session = agent.sessions.get_or_create(session_key)
        rows = session.messages[-limit:] if len(session.messages) > limit else session.messages
        return [
            {
                "role": item.get("role", "assistant"),
                "content": item.get("content", ""),
                "timestamp": item.get("timestamp"),
            }
            for item in rows
        ]


_CHAT_SERVICE: ChatService | None = None


def get_chat_service(config_loader) -> ChatService:
    global _CHAT_SERVICE
    if _CHAT_SERVICE is None:
        _CHAT_SERVICE = ChatService(config_loader)
    return _CHAT_SERVICE
