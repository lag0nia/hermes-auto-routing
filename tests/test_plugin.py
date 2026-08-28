from hermes_auto_routing import register


class FakeContext:
    def __init__(self) -> None:
        self.hooks: list[tuple[str, object]] = []

    def register_hook(self, name: str, callback: object) -> None:
        self.hooks.append((name, callback))


def test_registers_only_supported_gateway_hook() -> None:
    context = FakeContext()

    register(context)

    assert [name for name, _callback in context.hooks] == ["pre_gateway_dispatch"]
