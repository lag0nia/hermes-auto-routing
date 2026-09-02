# Hermes Auto Routing

A small, deterministic routing plugin for Hermes gateway messages. It assigns
only high-signal requests to a single specialist profile and leaves generic or
ambiguous messages on the current default path.

The plugin is intentionally conservative: routing is not capability granting,
and a route is applied only after the gateway has validated that the target
profile is served and allowed.

## What this repository contains

- `plugin.yaml`, the Hermes plugin manifest;
- `src/hermes_auto_routing/router.py`, the classifier and gateway hook;
- `tests/`, the routing behavior and integration contract tests;
- `pyproject.toml` and `uv.lock`, the Python project and locked development
  environment.

## How routing works

The plugin registers the `pre_gateway_dispatch` hook. For each inbound event it:

1. normalizes case, whitespace, and accents;
2. checks closed action/context rule sets;
3. returns a bounded route directive only when exactly one specialist rule
   matches;
4. leaves the event unchanged when no rule matches or multiple rules match;
5. never overwrites a profile that has already been explicitly assigned;
6. does not route when gateway profile multiplexing is disabled.

The resulting directive contains only an action and an intent. The original
message is not included in the directive.

## Example decisions

| Request shape | Result |
|---|---|
| Investigate error logs or exceptions | `researcher` / `technical.research` |
| Plan a system architecture | `architect-planner` / `technical.plan` |
| Implement a code function | `coder` / `code.change` |
| Update or query documentation | `documentator` / `docs.reconcile` or `docs.query` |
| Search or plan travel | `travel-planner` / matching travel intent |
| Interact with a web form | `browser-operator` / `browser.form.prepare` |
| Generic question or conflicting signals | unchanged; remains on the default path |

These are classifications, not approvals. The gateway and control plane must
still enforce profile allowlists, capability policy, risk checks, and user
confirmation for side effects.

## Quick start

Requirements: Python 3.13 and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest -q
uv run ruff check .
uv run mypy
```

## Integrating with Hermes

Install the reviewed plugin through Hermes' normal plugin mechanism. Enable
gateway profile multiplexing and explicitly serve the profiles that may receive
routes. The plugin's runtime entry point is:

```python
from hermes_auto_routing.router import register_hooks

register_hooks(context)
```

`context` must be the Hermes plugin context that provides `register_hook`.
The gateway remains responsible for validating the route target and enforcing
its own profile and capability policy.

## Security and privacy

The classifier does not read credentials, cookies, browser state, or full
conversation history. It does not persist inbound messages. Keep credentials
in Hermes' normal secret store or ignored local `.env` files; never commit
secrets, tokens, cookies, or authentication files.

## Contributing

Add regression tests for every new rule and run the complete quality gate before
sharing a commit:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy
```

Prefer one strong, unambiguous rule over broad keyword matching. Ambiguity must
remain visible to the gateway rather than being silently forced to a profile.
