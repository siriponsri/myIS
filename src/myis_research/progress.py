"""Privacy-safe progress reporting for long-running local workflows."""

from __future__ import annotations

import json
import re
import sys
import threading
import time
from collections.abc import Callable
from types import TracebackType
from typing import TextIO


PROGRESS_SCHEMA = "myis.progress.v1"
DEFAULT_HEARTBEAT_SECONDS = 120.0
MAX_ETA_SECONDS = 7 * 24 * 60 * 60
_STAGE_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")


class ProgressReporter:
    """Create single-stage progress tasks with TTY and JSONL rendering."""

    def __init__(
        self,
        *,
        stream: TextIO | None = None,
        heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS,
        interactive: bool | None = None,
        clock: Callable[[], float] = time.perf_counter,
        max_eta_seconds: float = MAX_ETA_SECONDS,
        tty_render_seconds: float = 0.25,
    ) -> None:
        if heartbeat_seconds <= 0:
            raise ValueError("heartbeat_seconds must be positive")
        if max_eta_seconds <= 0 or tty_render_seconds < 0:
            raise ValueError("progress timing bounds are invalid")
        self.stream = stream or sys.stderr
        self.heartbeat_seconds = float(heartbeat_seconds)
        self.interactive = self.stream.isatty() if interactive is None else bool(interactive)
        self.clock = clock
        self.max_eta_seconds = float(max_eta_seconds)
        self.tty_render_seconds = float(tty_render_seconds)

    def stage(self, stage: str, *, total: int) -> ProgressTask:
        return ProgressTask(self, stage=stage, total=total)


class ProgressTask:
    """One progress stage that emits no identifiers or item-level outcomes."""

    def __init__(self, reporter: ProgressReporter, *, stage: str, total: int) -> None:
        if not _STAGE_RE.fullmatch(stage):
            raise ValueError("progress stage must be a fixed lowercase safe label")
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise ValueError("progress total must be a non-negative integer")
        self._reporter = reporter
        self.stage = stage
        self.total = total
        self._processed = 0
        self._started_at = 0.0
        self._last_tty_render = float("-inf")
        self._entered = False
        self._closed = False
        self._output_disabled = False
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> ProgressTask:
        if self._entered:
            raise RuntimeError("progress task cannot be entered twice")
        self._entered = True
        self._started_at = self._reporter.clock()
        self._emit("started")
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"myis-progress-{self.stage}",
            daemon=True,
        )
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_value, traceback
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._emit("completed" if exc_type is None else "failed", final=True)
        self._closed = True

    @property
    def processed(self) -> int:
        with self._lock:
            return self._processed

    def advance(self, count: int = 1) -> None:
        if not self._entered or self._closed:
            raise RuntimeError("progress task is not active")
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ValueError("progress advance must be a positive integer")
        with self._lock:
            updated = self._processed + count
            if updated > self.total:
                raise ValueError("progress cannot exceed its declared total")
            self._processed = updated
            should_render = (
                self._reporter.interactive
                and (
                    self._processed == self.total
                    or self._reporter.clock() - self._last_tty_render >= self._reporter.tty_render_seconds
                )
            )
        if should_render:
            self._emit("running")

    def heartbeat(self) -> None:
        """Emit one on-demand heartbeat without changing the processed count."""

        if not self._entered or self._closed:
            raise RuntimeError("progress task is not active")
        self._emit("running")

    def _heartbeat_loop(self) -> None:
        while not self._stop.wait(self._reporter.heartbeat_seconds):
            self._emit("running")

    def _snapshot(self, status: str) -> dict[str, object]:
        now = self._reporter.clock()
        with self._lock:
            processed = self._processed
        elapsed = max(0.0, now - self._started_at)
        eta: float | None = None
        if status == "completed":
            eta = 0.0
        elif processed > 0 and processed < self.total and elapsed > 0:
            estimate = (self.total - processed) * elapsed / processed
            eta = min(max(0.0, estimate), self._reporter.max_eta_seconds)
        return {
            "elapsed_seconds": round(elapsed, 3),
            "eta_seconds": None if eta is None else round(eta, 3),
            "processed": processed,
            "schema_version": PROGRESS_SCHEMA,
            "stage": self.stage,
            "status": status,
            "total": self.total,
        }

    def _emit(self, status: str, *, final: bool = False) -> None:
        if self._output_disabled:
            return
        payload = self._snapshot(status)
        try:
            if self._reporter.interactive:
                self._write_tty(payload, final=final)
            else:
                self._reporter.stream.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")
                self._reporter.stream.flush()
        except (OSError, ValueError):
            self._output_disabled = True

    def _write_tty(self, payload: dict[str, object], *, final: bool) -> None:
        processed = int(payload["processed"])
        total = int(payload["total"])
        ratio = 1.0 if total == 0 else processed / total
        width = 24
        filled = min(width, max(0, int(ratio * width)))
        bar = "=" * filled + ">"[: int(filled < width)] + "." * max(0, width - filled - int(filled < width))
        elapsed = _format_seconds(float(payload["elapsed_seconds"]))
        eta_value = payload["eta_seconds"]
        eta = "--:--:--" if eta_value is None else _format_seconds(float(eta_value))
        suffix = "\n" if final else ""
        self._reporter.stream.write(
            f"\r{self.stage:<24} [{bar}] {processed:>6}/{total:<6} elapsed {elapsed} eta {eta}{suffix}"
        )
        self._reporter.stream.flush()
        self._last_tty_render = self._reporter.clock()


def _format_seconds(value: float) -> str:
    seconds = max(0, int(round(value)))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
