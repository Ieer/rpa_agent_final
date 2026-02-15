from __future__ import annotations

import concurrent.futures
import logging
import os
import time
from pathlib import Path
from typing import Any

import yaml

from core.registry import RPA_REGISTRY
from core.schema import Status

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def _prepare_logger() -> None:
    config = load_config()
    log_file = BASE_DIR / config["rpa"]["log_file"]
    os.makedirs(log_file.parent, exist_ok=True)
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )


_prepare_logger()


class RPAExecutor:
    @staticmethod
    def run(rpa_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        config = load_config()
        params = params or {}

        if rpa_name not in RPA_REGISTRY:
            return {"status": Status.NOT_FOUND, "rpa": rpa_name, "msg": "RPA 不存在"}

        entry = RPA_REGISTRY[rpa_name]
        func = entry["func"]
        max_retry = int(config["system"].get("max_retry", 2))
        timeout = int(config["system"].get("timeout", 60))

        for index in range(max_retry + 1):
            try:
                logging.info("執行 %s %s", rpa_name, params)
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(func, **params)
                    result = future.result(timeout=timeout)
                logging.info("成功 %s", rpa_name)
                return {"status": Status.SUCCESS, "rpa": rpa_name, "data": result}
            except concurrent.futures.TimeoutError:
                logging.error("逾時 %s 次數=%s", rpa_name, index + 1)
            except Exception as exc:
                logging.error("失敗 %s 次數=%s 錯誤=%s", rpa_name, index + 1, exc)

            if index < max_retry:
                time.sleep(1)

        return {"status": Status.FAILED, "rpa": rpa_name, "error": "重試耗盡"}
