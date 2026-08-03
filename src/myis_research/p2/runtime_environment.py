"""Allowlisted environment construction for detached P2 runtime processes."""

from __future__ import annotations

import os
import re
from typing import Mapping


_ALLOWED = frozenset(
    {
        "APPDATA",
        "CODEX_HOME",
        "COMSPEC",
        "HOME",
        "LANG",
        "LC_ALL",
        "LOCALAPPDATA",
        "PATH",
        "PATHEXT",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "VIRTUAL_ENV",
        "WINDIR",
    }
)
_CREDENTIAL_KEY = re.compile(
    r"(?:API[_-]?KEY|ACCESS[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|AUTH|COOKIE|SESSION)",
    re.IGNORECASE,
)


def sanitized_runtime_environment(
    source: Mapping[str, str] | None = None,
) -> dict[str, str]:
    values = dict(os.environ if source is None else source)
    output: dict[str, str] = {}
    for key in sorted(values):
        upper = key.upper()
        if upper not in _ALLOWED or _CREDENTIAL_KEY.search(upper):
            continue
        if upper in {"MYIS_STORE", "MYIS_MLFLOW_STORE"}:
            continue
        output[key] = str(values[key])
    output.setdefault("PYTHONUTF8", "1")
    output.setdefault("PYTHONIOENCODING", "utf-8")
    return output
