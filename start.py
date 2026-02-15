from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path
from typing import Any

import uvicorn
import yaml
from nanobot_bridge.config_mapper import map_config_to_nanobot_runtime
from nanobot_tool import register_rpa_tool

BASE_DIR = Path(__file__).resolve().parent
LOCAL_NANOBOT_ROOT = BASE_DIR / "nanobot"

if LOCAL_NANOBOT_ROOT.exists() and str(LOCAL_NANOBOT_ROOT) not in sys.path:
    sys.path.insert(0, str(LOCAL_NANOBOT_ROOT))


def load_config() -> dict[str, Any]:
    with (BASE_DIR / "config.yaml").open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def start_api() -> None:
    from adapter.api import app

    config = load_config()
    uvicorn.run(app, host=config["api"]["host"], port=int(config["api"]["port"]))


def _build_provider(config: dict[str, Any]):
    from nanobot.providers.litellm_provider import LiteLLMProvider

    runtime = map_config_to_nanobot_runtime(config)
    provider_cfg = runtime.provider

    return LiteLLMProvider(
        api_key=provider_cfg.api_key,
        api_base=provider_cfg.api_base,
        default_model=provider_cfg.default_model,
        extra_headers=provider_cfg.extra_headers,
        provider_name=provider_cfg.provider_name,
    )


async def _run_agent_loop(config: dict[str, Any]) -> None:
    from nanobot.agent.loop import AgentLoop
    from nanobot.bus.queue import MessageBus

    runtime = map_config_to_nanobot_runtime(config)

    bus = MessageBus()
    provider = _build_provider(config)

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

    print("NanoBot Agent 已启动（输入 exit 退出）")
    while True:
        try:
            message = input("You> ").strip()
        except EOFError:
            break

        if not message:
            continue
        if message.lower() in {"exit", "quit"}:
            break

        response = await agent.process_direct(message, session_key="cli:rpa")
        print(f"Bot> {response}")


def start_agent() -> None:
    config = load_config()
    asyncio.run(_run_agent_loop(config))


if __name__ == "__main__":
    cfg = load_config()
    print("RPA Agent 最終版啟動中...")

    if cfg["system"].get("mode") == "api":
        threading.Thread(target=start_api, daemon=True).start()

    start_agent()
