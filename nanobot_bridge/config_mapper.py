from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderRuntimeConfig:
    api_key: str | None
    api_base: str | None
    default_model: str
    extra_headers: dict[str, str]
    provider_name: str | None


@dataclass
class AgentRuntimeConfig:
    max_iterations: int
    memory_window: int
    restrict_to_workspace: bool


@dataclass
class NanobotRuntimeConfig:
    provider: ProviderRuntimeConfig
    agent: AgentRuntimeConfig


def _safe_import_registry():
    from nanobot.providers.registry import find_by_model, find_by_name

    return find_by_model, find_by_name


def _normalize_headers(raw: Any) -> dict[str, str]:
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}
    return {}


def _route_model(llm_cfg: dict[str, Any]) -> str:
    model = str(llm_cfg.get("model", "qwen2:1.5b"))
    routes = llm_cfg.get("model_routes", {})

    if isinstance(routes, dict) and model in routes:
        return str(routes[model])

    if isinstance(routes, list):
        for rule in routes:
            if not isinstance(rule, dict):
                continue
            if str(rule.get("from", "")) == model and rule.get("to"):
                return str(rule["to"])

    return model


def _resolve_provider_name(llm_cfg: dict[str, Any], model: str) -> str | None:
    find_by_model, find_by_name = _safe_import_registry()

    explicit = llm_cfg.get("provider")
    if explicit:
        spec = find_by_name(str(explicit))
        if spec:
            return spec.name

    base_url = str(llm_cfg.get("base_url", "") or "").lower()
    if base_url:
        if "127.0.0.1" in base_url or "localhost" in base_url or "ollama" in base_url:
            return "custom"

    spec = find_by_model(model)
    return spec.name if spec else None


def map_config_to_nanobot_runtime(config: dict[str, Any]) -> NanobotRuntimeConfig:
    llm_cfg = config.get("llm", {})
    model = _route_model(llm_cfg)
    provider_name = _resolve_provider_name(llm_cfg, model)

    headers = _normalize_headers(llm_cfg.get("headers") or llm_cfg.get("extra_headers"))

    provider = ProviderRuntimeConfig(
        api_key=llm_cfg.get("api_key"),
        api_base=llm_cfg.get("base_url"),
        default_model=model,
        extra_headers=headers,
        provider_name=provider_name,
    )

    agent = AgentRuntimeConfig(
        max_iterations=int(llm_cfg.get("max_tool_iterations", 20)),
        memory_window=int(llm_cfg.get("memory_window", 50)),
        restrict_to_workspace=bool(config.get("system", {}).get("restrict_to_workspace", False)),
    )

    return NanobotRuntimeConfig(provider=provider, agent=agent)
