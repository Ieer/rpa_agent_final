from __future__ import annotations

from typing import Any

from core.executor import RPAExecutor


class SkillAdapter:
    @staticmethod
    def run(rpa_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return RPAExecutor.run(rpa_name, params)
