"""Conservative content routing for the gateway profile boundary."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RouteDisposition(StrEnum):
    DEFAULT = "default"
    SPECIALIST = "specialist"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class RouteDecision:
    disposition: RouteDisposition
    profile: str | None
    intent: str | None
    reason: str


_RESEARCH_ACTIONS = (
    r"\bmira\b",
    r"\brevisa\b",
    r"\binvestiga\w*\b",
    r"\banaliza\w*\b",
    r"\bdiagnostica\w*\b",
    r"\bcomprueba\w*\b",
    r"\baverigua\w*\b",
    r"\bexplica\w*\b",
    r"\bpor que\b",
    r"\bque paso\b",
    r"\bque ha pasado\b",
)
_RESEARCH_EVIDENCE = (
    r"\blogs?\b",
    r"\bregistros?\b",
    r"\btrazas?\b",
    r"\berror(?:es)?\b",
    r"\bfallo(?:s)?\b",
    r"\bexcepcion(?:es)?\b",
    r"\bstack trace\b",
    r"\bcrash(?:es)?\b",
)
_ENGINEER_CHANGE_ACTIONS = (
    r"\bcorrige\w*\b",
    r"\barregla\w*\b",
    r"\bimplementa\w*\b",
    r"\bmodifica\w*\b",
    r"\bcambia\w*\b",
    r"\bconfigura\w*\b",
    r"\brepara\w*\b",
)
_ENGINEER_REVIEW_ACTIONS = (
    r"\brevisa\w*\b",
    r"\baudita\w*\b",
    r"\binspecciona\w*\b",
    r"\bevalua\w*\b",
)
_ENGINEER_CONTEXT = (
    r"\bcodigo\b",
    r"\bimplementacion\b",
    r"\bconfiguracion\b",
    r"\bbridge\b",
    r"\brouter\b",
    r"\bmcp\b",
    r"\bplugin(?:s)?\b",
    r"\btest(?:s)?\b",
    r"\bintegracion\b",
    r"\bsistema\b",
    r"\bbug\b",
)


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.casefold()).strip()


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_message(text: str) -> RouteDecision:
    normalized = _normalize(text)
    candidates: list[tuple[str, str]] = []

    if _matches(normalized, _RESEARCH_ACTIONS) and _matches(normalized, _RESEARCH_EVIDENCE):
        candidates.append(("researcher", "technical.research"))

    engineer_action = _matches(normalized, _ENGINEER_CHANGE_ACTIONS) or (
        _matches(normalized, _ENGINEER_REVIEW_ACTIONS)
        and _matches(normalized, _ENGINEER_CONTEXT)
    )
    if engineer_action and _matches(normalized, _ENGINEER_CONTEXT):
        candidates.append(("engineer", "technical.change"))

    if not candidates:
        return RouteDecision(
            RouteDisposition.DEFAULT,
            None,
            None,
            "no unique specialist rule matched",
        )
    if len(candidates) > 1:
        return RouteDecision(
            RouteDisposition.AMBIGUOUS,
            None,
            None,
            "multiple specialist rules matched",
        )
    profile, intent = candidates[0]
    return RouteDecision(
        RouteDisposition.SPECIALIST,
        profile,
        intent,
        "one deterministic specialist rule matched",
    )


def route_from_event(**kwargs: Any) -> dict[str, str] | None:
    """Stamp a concrete profile before the gateway's normal dispatch path."""
    event = kwargs.get("event")
    gateway = kwargs.get("gateway")
    source = getattr(event, "source", None)
    if (
        source is None
        or getattr(source, "profile", None)
        or not getattr(getattr(gateway, "config", None), "multiplex_profiles", False)
    ):
        return None
    text = getattr(event, "text", "")
    if not isinstance(text, str) or not text:
        return None
    decision = classify_message(text)
    if decision.disposition is not RouteDisposition.SPECIALIST or decision.profile is None:
        return None
    source.profile = decision.profile
    return {
        "action": "allow",
        "intent": decision.intent or "",
    }


def register_hooks(ctx: Any) -> None:
    register: Callable[..., Any] = ctx.register_hook
    register("pre_gateway_dispatch", route_from_event)


__all__ = ["RouteDecision", "RouteDisposition", "classify_message", "route_from_event"]
