"""Loopback transport, session, CSRF, and Windows actor controls."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware


SECURITY_HEADERS = {
    "Cache-Control": "no-store, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
    "Content-Security-Policy": "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

_INTERACTIVE_STATES = frozenset({0, 1, 2, 3, 4, 5})
_BROAD_WRITE_SIDS = frozenset({"S-1-1-0", "S-1-5-11", "S-1-5-32-545"})
_WRITE_RIGHTS_MASK = 2 | 4 | 16 | 256 | 65536 | 262144 | 524288


@dataclass(frozen=True, slots=True)
class WindowsSession:
    session_id: int
    station_name: str
    state: int
    username: str
    current: bool


class LoopbackSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, *, origin: str, test_mode: bool = False) -> None:
        super().__init__(app)
        self.origin = origin
        self.expected_host = origin.removeprefix("http://")
        self.test_mode = test_mode

    async def dispatch(self, request: Request, call_next: Any):
        peer = request.client.host if request.client else ""
        if not self.test_mode and peer != "127.0.0.1":
            return self._reject(403, "loopback client required")
        if request.headers.get("host") != self.expected_host:
            return self._reject(400, "invalid Host")
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.headers.get("origin") != self.origin:
                return self._reject(403, "invalid Origin")
        response = await call_next(request)
        self._add_security_headers(response)
        return response

    @staticmethod
    def _add_security_headers(response: Response) -> None:
        for name, value in SECURITY_HEADERS.items():
            response.headers[name] = value

    def _reject(self, status_code: int, detail: str) -> JSONResponse:
        response = JSONResponse({"detail": detail}, status_code=status_code)
        self._add_security_headers(response)
        return response


@dataclass
class Session:
    csrf: str
    expires_at: float


class SessionStore:
    def __init__(self, *, ttl_seconds: int = 1800) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, Session] = {}

    def create(self) -> tuple[str, Session]:
        session_id = secrets.token_urlsafe(32)
        session = Session(secrets.token_urlsafe(32), time() + self.ttl_seconds)
        self._sessions[session_id] = session
        return session_id, session

    def require(self, request: Request, *, csrf: bool = False) -> tuple[str, Session]:
        session_id = request.cookies.get("myis_session")
        session = self._sessions.get(session_id or "")
        if session is None or session.expires_at < time():
            raise HTTPException(status_code=401, detail="valid local session required")
        if csrf and request.headers.get("x-csrf-token") != session.csrf:
            raise HTTPException(status_code=403, detail="invalid CSRF token")
        return session_id or "", session


def authoritative_actor_id(state_root: Path, *, sid_override: str | None = None) -> str:
    state_root.mkdir(parents=True, exist_ok=True)
    salt_path = state_root / "actor-salt.bin"
    if not salt_path.exists():
        with salt_path.open("xb") as stream:
            stream.write(secrets.token_bytes(32))
    salt = salt_path.read_bytes()
    sid = sid_override or windows_account_sid()
    return hashlib.sha256(b"myis-dashboard-actor-v1\0" + salt + sid.encode("utf-8")).hexdigest()


def windows_account_sid() -> str:
    if os.name != "nt":
        raise RuntimeError("dashboard authoritative identity requires Windows")
    completed = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    columns = [item.strip().strip('"') for item in completed.stdout.strip().split(",")]
    if len(columns) < 2 or not columns[1].startswith("S-"):
        raise RuntimeError("cannot resolve authoritative Windows SID")
    return columns[1]


def assert_local_single_user_session() -> None:
    if os.name != "nt":
        raise RuntimeError("dashboard is restricted to a local Windows console session")
    if os.environ.get("SESSIONNAME", "").casefold() != "console":
        raise RuntimeError("dashboard refuses remote or non-console Windows sessions")
    _validate_session_snapshot(_enumerate_windows_sessions())


def _validate_session_snapshot(sessions: list[WindowsSession]) -> None:
    interactive = [
        item for item in sessions if item.username.strip() and item.state in _INTERACTIVE_STATES
    ]
    current = [item for item in interactive if item.current]
    if len(current) != 1:
        raise RuntimeError("cannot identify exactly one current interactive Windows session")
    if current[0].station_name.casefold() != "console" or current[0].state != 0:
        raise RuntimeError("dashboard requires the active local Console session")
    if len(interactive) != 1:
        raise RuntimeError("dashboard refuses multi-user Windows operation")


def _enumerate_windows_sessions() -> list[WindowsSession]:
    import ctypes
    from ctypes import wintypes

    class WtsSessionInfo(ctypes.Structure):
        _fields_ = [
            ("session_id", wintypes.DWORD),
            ("station_name", wintypes.LPWSTR),
            ("state", ctypes.c_int),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    wtsapi32 = ctypes.WinDLL("wtsapi32", use_last_error=True)
    kernel32.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel32.ProcessIdToSessionId.restype = wintypes.BOOL
    wtsapi32.WTSEnumerateSessionsW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(WtsSessionInfo)),
        ctypes.POINTER(wintypes.DWORD),
    ]
    wtsapi32.WTSEnumerateSessionsW.restype = wintypes.BOOL
    wtsapi32.WTSQuerySessionInformationW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.DWORD),
    ]
    wtsapi32.WTSQuerySessionInformationW.restype = wintypes.BOOL
    wtsapi32.WTSFreeMemory.argtypes = [ctypes.c_void_p]

    current_id = wintypes.DWORD()
    if not kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(current_id)):
        raise RuntimeError("cannot resolve the current Windows session")

    pointer = ctypes.POINTER(WtsSessionInfo)()
    count = wintypes.DWORD()
    if not wtsapi32.WTSEnumerateSessionsW(None, 0, 1, ctypes.byref(pointer), ctypes.byref(count)):
        raise RuntimeError("cannot enumerate Windows sessions")
    sessions: list[WindowsSession] = []
    try:
        for index in range(count.value):
            item = pointer[index]
            username_pointer = ctypes.c_void_p()
            byte_count = wintypes.DWORD()
            username = ""
            if wtsapi32.WTSQuerySessionInformationW(
                None, item.session_id, 5, ctypes.byref(username_pointer), ctypes.byref(byte_count)
            ):
                try:
                    if username_pointer.value:
                        username = ctypes.wstring_at(username_pointer.value)
                finally:
                    if username_pointer.value:
                        wtsapi32.WTSFreeMemory(username_pointer)
            sessions.append(
                WindowsSession(
                    session_id=int(item.session_id),
                    station_name=item.station_name or "",
                    state=int(item.state),
                    username=username,
                    current=int(item.session_id) == current_id.value,
                )
            )
    finally:
        wtsapi32.WTSFreeMemory(ctypes.cast(pointer, ctypes.c_void_p))
    return sessions


def assert_private_root_acl(root: Path, *, expected_owner_sid: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.resolve(strict=True).is_dir():
        raise RuntimeError("dashboard private root must be a regular directory")
    if os.name != "nt":
        raise RuntimeError("dashboard private-root ACL validation requires Windows")
    script = (
        "$acl=Get-Acl -LiteralPath $env:MYIS_DASHBOARD_ACL_PATH;"
        "$owner=$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value;"
        "$rules=@($acl.Access|ForEach-Object{[pscustomobject]@{"
        "sid=$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value;"
        "rights=[int]$_.FileSystemRights;type=$_.AccessControlType.ToString()}});"
        "[pscustomobject]@{owner_sid=$owner;rules=$rules}|ConvertTo-Json -Compress -Depth 4"
    )
    environment = os.environ.copy()
    environment["MYIS_DASHBOARD_ACL_PATH"] = str(root.resolve(strict=True))
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
        env=environment,
    )
    if completed.returncode != 0:
        error_type = completed.stderr.strip().splitlines()[0] if completed.stderr.strip() else "unknown error"
        raise RuntimeError(f"dashboard private-root ACL inspection failed: {error_type}")
    payload = json.loads(completed.stdout)
    if payload.get("owner_sid") != expected_owner_sid:
        raise RuntimeError("dashboard private root is not owned by the backend Windows account")
    rules = payload.get("rules", [])
    if isinstance(rules, dict):
        rules = [rules]
    for rule in rules:
        if (
            rule.get("type") == "Allow"
            and rule.get("sid") in _BROAD_WRITE_SIDS
            and int(rule.get("rights", 0)) & _WRITE_RIGHTS_MASK
        ):
            raise RuntimeError("dashboard private root grants broad write access")
