from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from nanobot_tool import execute_rpa


class Workflow:
    @staticmethod
    def run(task_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        run_id = uuid4().hex
        result: list[dict[str, Any]] = []
        for index, task in enumerate(task_list, start=1):
            task_name = task["name"]
            task_params = task.get("params")
            step_id = f"step-{index}"
            started_at = datetime.now(timezone.utc)
            started_counter = perf_counter()
            logging.info("workflow_start run_id=%s step_id=%s name=%s params=%s", run_id, step_id, task_name, task_params)
            try:
                raw_result = execute_rpa(task_name, task_params)
                ended_at = datetime.now(timezone.utc)
                duration_ms = int((perf_counter() - started_counter) * 1000)

                if isinstance(raw_result, dict):
                    status = str(raw_result.get("status", "success"))
                    error_message = raw_result.get("error")
                else:
                    status = "success"
                    error_message = None

                logging.info(
                    "workflow_end run_id=%s step_id=%s status=%s duration_ms=%s",
                    run_id,
                    step_id,
                    status,
                    duration_ms,
                )

                result.append(
                    {
                        "run_id": run_id,
                        "step_id": step_id,
                        "step_index": index,
                        "name": task_name,
                        "params": task_params,
                        "status": status,
                        "started_at": started_at.isoformat(),
                        "ended_at": ended_at.isoformat(),
                        "duration_ms": duration_ms,
                        "error_code": "EXECUTION_FAILED" if status == "failed" else None,
                        "error_message": error_message,
                        "result": raw_result,
                    }
                )
            except Exception as exc:
                ended_at = datetime.now(timezone.utc)
                duration_ms = int((perf_counter() - started_counter) * 1000)
                logging.exception(
                    "workflow_exception run_id=%s step_id=%s duration_ms=%s error=%s",
                    run_id,
                    step_id,
                    duration_ms,
                    exc,
                )
                result.append(
                    {
                        "run_id": run_id,
                        "step_id": step_id,
                        "step_index": index,
                        "name": task_name,
                        "params": task_params,
                        "status": "failed",
                        "started_at": started_at.isoformat(),
                        "ended_at": ended_at.isoformat(),
                        "duration_ms": duration_ms,
                        "error_code": "WORKFLOW_EXCEPTION",
                        "error_message": str(exc),
                        "result": None,
                    }
                )
        return result
