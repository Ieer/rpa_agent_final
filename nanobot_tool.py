from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import requests
import yaml

from adapter.skill import SkillAdapter

BASE_DIR = Path(__file__).resolve().parent
LOCAL_NANOBOT_ROOT = BASE_DIR / "nanobot"

if LOCAL_NANOBOT_ROOT.exists() and str(LOCAL_NANOBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_NANOBOT_ROOT))

from nanobot.agent.tools.base import Tool


def load_config() -> dict[str, Any]:
    with (BASE_DIR / "config.yaml").open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def execute_rpa(rpa_name: str, params: dict[str, Any] | None = None):
    params = params or {}
    config = load_config()
    mode = config["system"].get("mode", "skill")

    if mode == "skill":
        return SkillAdapter.run(rpa_name, params)

    api = config["api"]
    api_url = f"http://{api['host']}:{api['port']}/api/rpa/run"
    response = requests.post(
        api_url,
        json={"rpa_name": rpa_name, "params": params},
        headers={"api_key": api["api_key"]},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


class ExecuteRPATool(Tool):
    @property
    def name(self) -> str:
        return "execute_rpa"

    @property
    def description(self) -> str:
        return "Execute a registered RPA task by name with optional params"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rpa_name": {
                    "type": "string",
                    "description": "Registered RPA name in core.registry.RPA_REGISTRY",
                },
                "params": {
                    "type": "object",
                    "description": "RPA input parameters",
                    "default": {},
                },
            },
            "required": ["rpa_name"],
        }

    async def execute(self, **kwargs: Any) -> str:
        result = execute_rpa(kwargs["rpa_name"], kwargs.get("params"))
        return json.dumps(result, ensure_ascii=False)


def register_rpa_tool(tool_registry: Any) -> None:
    if not tool_registry.has("execute_rpa"):
        tool_registry.register(ExecuteRPATool())
