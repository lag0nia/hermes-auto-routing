from types import SimpleNamespace

import pytest

from hermes_auto_routing.router import (
    RouteDisposition,
    classify_message,
    route_from_event,
)


def event(text: str, profile: str | None = None):
    return SimpleNamespace(text=text, source=SimpleNamespace(profile=profile))


def gateway(multiplex_profiles: bool = True):
    return SimpleNamespace(config=SimpleNamespace(multiplex_profiles=multiplex_profiles))


def test_travel_plan_routes_to_the_travel_planner_profile() -> None:
    inbound = event("Planea un viaje a Lisboa con vuelos y alojamiento")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "travel-planner"
    assert decision.intent == "travel.plan"
    assert result == {"action": "allow", "intent": "travel.plan"}
    assert inbound.source.profile == "travel-planner"


def test_browser_interaction_routes_to_the_browser_operator_profile() -> None:
    inbound = event("Abre el navegador e interactúa con el formulario de reserva")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "browser-operator"
    assert decision.intent == "browser.form.prepare"
    assert result == {"action": "allow", "intent": "browser.form.prepare"}
    assert inbound.source.profile == "browser-operator"


def test_documentation_request_routes_to_the_documentator_profile() -> None:
    inbound = event("Actualiza la documentación y el README del harness")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "documentator"
    assert decision.intent == "docs.reconcile"
    assert result == {"action": "allow", "intent": "docs.reconcile"}
    assert inbound.source.profile == "documentator"


def test_generic_question_uses_the_default_fallback_without_profile_mutation() -> None:
    inbound = event("¿Qué es este servicio?")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.DEFAULT
    assert decision.profile is None
    assert decision.intent is None
    assert result is None
    assert inbound.source.profile is None


def test_technical_research_routes_to_the_researcher_profile() -> None:
    inbound = event("Mira los logs del servicio y dime por qué fallaron")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "researcher"
    assert decision.intent == "technical.research"
    assert result == {"action": "allow", "intent": "technical.research"}
    assert inbound.source.profile == "researcher"


def test_mcp_bridge_diagnosis_routes_to_the_researcher_profile() -> None:
    inbound = event("Investiga por qué falla el bridge MCP")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "researcher"
    assert decision.intent == "technical.research"
    assert result == {"action": "allow", "intent": "technical.research"}
    assert inbound.source.profile == "researcher"


def test_technical_change_routes_to_the_engineer_profile() -> None:
    inbound = event("Corrige el código del router que falla")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "engineer"
    assert decision.intent == "technical.change"
    assert result == {"action": "allow", "intent": "technical.change"}
    assert inbound.source.profile == "engineer"


def test_ambiguous_message_uses_the_ambiguous_fallback_without_profile_mutation() -> None:
    inbound = event("Revisa los logs y corrige el código si hace falta")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.AMBIGUOUS
    assert decision.profile is None
    assert decision.intent is None
    assert result is None
    assert inbound.source.profile is None


def test_explicit_profile_wins_over_a_direct_route() -> None:
    inbound = event("Mira los logs del servicio y dime por qué fallaron", profile="coder")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "researcher"
    assert decision.intent == "technical.research"
    assert result is None
    assert inbound.source.profile == "coder"


def test_disabled_multiplexing_leaves_the_source_profile_unchanged() -> None:
    inbound = event("Mira los logs del servicio y dime por qué fallaron")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway(False))

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "researcher"
    assert decision.intent == "technical.research"
    assert result is None
    assert inbound.source.profile is None


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


def test_development_coordinate_routes_to_the_default_profile() -> None:
    inbound = event("crear un plugin para el sistema con password=secret")

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "default"
    assert decision.intent == "development.coordinate"
    assert result == {"action": "allow", "intent": "development.coordinate"}
    assert inbound.source.profile == "default"
    assert "password" not in str(result)
    assert "secret" not in str(result)


@pytest.mark.parametrize(
    ("message", "profile", "intent"),
    [
        ("crear un plugin para el sistema", "default", "development.coordinate"),
        ("vamos a desarrollar una nueva integración", "default", "development.coordinate"),
        (
            "IMPLEMENTA una integración y revisa los logs",
            "default",
            "development.coordinate",
        ),
        (
            "DISEÑA la arquitectura y el plan técnico del servicio",
            "architect-planner",
            "technical.plan",
        ),
        ("PLANIFICA el código del router", "coder", "code.plan"),
        ("IMPLEMENTA la función de autenticación", "coder", "code.change"),
        ("REVISA el código del router", "coder", "code.review"),
        ("Corrige el bug del router", "engineer", "technical.change"),
        ("Consulta la documentación del README", "documentator", "docs.query"),
        ("Abre el navegador y rellena el formulario", "browser-operator", "browser.form.prepare"),
        ("Planea un viaje a Lisboa", "travel-planner", "travel.plan"),
        ("Pregunto por viajes a Lisboa", "travel-planner", "travel.plan"),
        (
            "Ejecuta una interacción con el navegador",
            "browser-operator",
            "browser.form.prepare",
        ),
        ("Documenta el cambio", "documentator", "docs.reconcile"),
    ],
)
def test_classification_contract_matrix(
    message: str, profile: str, intent: str
) -> None:
    decision = classify_message(message)

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == profile
    assert decision.intent == intent


@pytest.mark.parametrize("message", ["Pregunto por el navegador", "Escribe el cambio"])
def test_generic_question_and_writing_stay_on_default(message: str) -> None:
    inbound = event(message)

    decision = classify_message(inbound.text)
    result = route_from_event(event=inbound, gateway=gateway())

    assert decision.disposition is RouteDisposition.DEFAULT
    assert decision.profile is None
    assert decision.intent is None
    assert result is None
    assert inbound.source.profile is None


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("Planea un viaje a Lisboa con vuelos y alojamiento", "travel.plan"),
        ("SEARCH FLIGHTS to Lisbon", "travel.search_flights"),
        ("Busca ALOJAMIENTO en Lisboa", "travel.search_stays"),
    ],
)
def test_explicit_travel_chooses_the_matching_travel_intent(
    message: str, intent: str
) -> None:
    decision = classify_message(message)

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "travel-planner"
    assert decision.intent == intent


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("Abre el navegador y rellena el formulario", "browser.form.prepare"),
        ("RESEARCH supplier prices in the BROWSER", "browser.research"),
    ],
)
def test_explicit_browser_work_chooses_the_matching_browser_intent(
    message: str, intent: str
) -> None:
    decision = classify_message(message)

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "browser-operator"
    assert decision.intent == intent


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("Actualiza la documentación del README", "docs.reconcile"),
        ("QUERY the API documentation", "docs.query"),
    ],
)
def test_explicit_documentation_work_chooses_the_matching_documentation_intent(
    message: str, intent: str
) -> None:
    decision = classify_message(message)

    assert decision.disposition is RouteDisposition.SPECIALIST
    assert decision.profile == "documentator"
    assert decision.intent == intent
