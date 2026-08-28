from types import SimpleNamespace

from hermes_auto_routing.router import (
    RouteDisposition,
    classify_message,
    route_from_event,
)


def event(text: str, profile: str | None = None):
    return SimpleNamespace(text=text, source=SimpleNamespace(profile=profile))


def gateway(multiplex_profiles: bool = True):
    return SimpleNamespace(config=SimpleNamespace(multiplex_profiles=multiplex_profiles))


def test_log_diagnosis_routes_to_researcher() -> None:
    decision = classify_message("Mira los logs de Uber Eats y dime por qué fallaron")

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "researcher"
    assert decision.intent == "technical.research"


def test_generic_question_stays_unrouted() -> None:
    decision = classify_message("¿Qué es Uber Eats?")

    assert decision.disposition is RouteDisposition.DEFAULT
    assert decision.profile is None
    assert decision.intent is None


def test_ambiguous_message_stays_unrouted() -> None:
    decision = classify_message("Revisa los logs y corrige el código si hace falta")

    assert decision.disposition is RouteDisposition.AMBIGUOUS
    assert decision.profile is None


def test_explicit_profile_route_wins() -> None:
    assert (
        route_from_event(event=event("Mira los logs", profile="coder"), gateway=gateway()) is None
    )


def test_simple_gateway_does_not_route_content() -> None:
    assert route_from_event(event=event("Mira los logs"), gateway=gateway(False)) is None


def test_route_directive_is_bounded_and_does_not_include_message() -> None:
    inbound = event("Mira los logs con password=secret")
    result = route_from_event(event=inbound, gateway=gateway())

    assert result == {
        "action": "allow",
        "intent": "technical.research",
    }
    assert inbound.source.profile == "researcher"
    assert "password" not in str(result)
    assert "secret" not in str(result)
