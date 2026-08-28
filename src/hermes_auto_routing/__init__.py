"""Native Hermes plugin registration entry point."""

from __future__ import annotations

from typing import Any

from .router import register_hooks


def register(ctx: Any) -> None:
    register_hooks(ctx)


__all__ = ["register"]
