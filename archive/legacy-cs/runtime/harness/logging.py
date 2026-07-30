"""One-event structured logging to console, runtime JSONL, and progress JSONL."""

from __future__ import annotations

import logging
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog


SCHEMA_VERSION = "myis.run-event.v1"
_SECRET_KEY = re.compile(
    r"(?:api[_-]?key|authorization|cookie|password|secret|token|private[_-]?key|ssh[_-]?key)",
    re.IGNORECASE,
)
_SECRET_VALUE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._~+/-]{8,}|(?:sk|ghp|pat)[-_][a-z0-9_-]{8,}|password\s*[=:]\s*\S+)"
)


def redact(value: Any, *, key: str = "") -> Any:
    """Recursively redact common credential fields and token-like strings."""
    if _SECRET_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return _SECRET_VALUE.sub("[REDACTED]", value)
    return value


def _redact_processor(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    return redact(event_dict)


def _drop_internal(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    event_dict.pop("_milestone", None)
    return event_dict


class _MilestoneOnly(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return isinstance(record.msg, dict) and bool(record.msg.get("_milestone"))


class RunLogger:
    """Run-scoped logger with a monotonic sequence and shared event IDs."""

    def __init__(self, run_dir: Path, *, run_id: str, goal_id: str, phase: str, component: str = "harness"):
        self.run_dir = run_dir
        self.run_id = run_id
        self.goal_id = goal_id
        self.phase = phase
        self.component = component
        self._sequence = 0
        self._lock = threading.Lock()
        self._handlers: list[logging.Handler] = []

        standard = logging.getLogger(f"myis.harness.{run_id}.{uuid.uuid4().hex}")
        standard.setLevel(logging.DEBUG)
        standard.propagate = False
        self._standard = standard

        shared = [
            structlog.contextvars.merge_contextvars,
            _redact_processor,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]
        self._logger = structlog.wrap_logger(standard, processors=shared)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processors=[
                    _drop_internal,
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=False),
                ]
            )
        )
        self._attach(standard, console)

        runtime = logging.FileHandler(run_dir / "runtime.jsonl", encoding="utf-8")
        runtime.setLevel(logging.DEBUG)
        runtime.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processors=[
                    _drop_internal,
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(sort_keys=True),
                ]
            )
        )
        self._attach(standard, runtime)

        progress = logging.FileHandler(run_dir / "progress.jsonl", encoding="utf-8")
        progress.setLevel(logging.DEBUG)
        progress.addFilter(_MilestoneOnly())
        progress.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processors=[
                    _drop_internal,
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(sort_keys=True),
                ]
            )
        )
        self._attach(standard, progress)

    def _attach(self, logger: logging.Logger, handler: logging.Handler) -> None:
        logger.addHandler(handler)
        self._handlers.append(handler)

    def emit(
        self,
        event: str,
        *,
        status: str,
        level: str = "info",
        milestone: bool = False,
        **details: Any,
    ) -> str:
        with self._lock:
            self._sequence += 1
            sequence = self._sequence
        event_id = str(uuid.uuid4())
        payload = {
            "schema_version": SCHEMA_VERSION,
            "event_id": event_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "monotonic_ns": time.monotonic_ns(),
            "sequence": sequence,
            "level": level.upper(),
            "run_id": self.run_id,
            "goal_id": self.goal_id,
            "phase": self.phase,
            "component": self.component,
            "status": status,
            "_milestone": milestone,
            **details,
        }
        getattr(self._logger, level)(event, **payload)
        return event_id

    def close(self) -> None:
        for handler in self._handlers:
            handler.flush()
            handler.close()
        for handler in self._handlers:
            self._standard.removeHandler(handler)

    def __enter__(self) -> "RunLogger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
