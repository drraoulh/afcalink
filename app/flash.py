from typing import Any

from fastapi import Request


def _add_flash(request: Request, category: str, message: str) -> None:
    flashes = request.session.get("flashes")
    if not isinstance(flashes, list):
        flashes = []
    flashes.append({"category": category, "message": message})
    request.session["flashes"] = flashes


def flash_success(request: Request, message: str) -> None:
    _add_flash(request, "success", message)


def flash_error(request: Request, message: str) -> None:
    _add_flash(request, "danger", message)


def flash_info(request: Request, message: str) -> None:
    _add_flash(request, "info", message)


def pop_flashes(request: Request) -> list[dict[str, Any]]:
    flashes = request.session.get("flashes")
    request.session["flashes"] = []
    if not isinstance(flashes, list):
        return []
    cleaned: list[dict[str, Any]] = []
    for f in flashes:
        if isinstance(f, dict) and f.get("message"):
            cleaned.append({"category": f.get("category") or "info", "message": str(f.get("message"))})
    return cleaned
