# hermes-auto-routing

Deterministic content routing for Hermes gateway messages. It routes only
unique high-signal technical requests to a concrete profile and leaves generic
or ambiguous messages on the current default profile.

The plugin does not read credentials, cookies, browser state, or full
conversation history. It returns a bounded route directive; the gateway is
responsible for validating the target against served profiles.
