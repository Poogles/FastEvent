import pytest
from pydantic import BaseModel

from fastevent import EventRouter, Route


class InputModel(BaseModel):
    foo: str
    bar: int


class OutputModel(BaseModel):
    baz: str


def test_event_router_registers_route() -> None:
    router = EventRouter()

    @router.event_handler(topic="topic1", subscription="sub1")
    def test_handler(input: InputModel) -> OutputModel:
        return OutputModel(baz="ok")

    assert len(router.routes) == 1
    route = router.routes[("topic1", "sub1")]

    assert isinstance(route, Route)
    assert route.topic == "topic1"
    assert route.subscription == "sub1"
    assert route.handler.__name__ == "test_handler"
    assert route.input_model == InputModel
    assert route.output_model == OutputModel


def test_event_router_handler_input_only() -> None:
    router = EventRouter()

    @router.event_handler(topic="topic2", subscription="sub2")
    def handler(input: InputModel):
        return None

    route = router.routes[("topic2", "sub2")]
    assert route.input_model == InputModel
    assert route.output_model is None


def test_event_router_handler_output_only() -> None:
    router = EventRouter()

    @router.event_handler(topic="topic3", subscription="sub3")
    def handler() -> OutputModel:
        return OutputModel(baz="ok")

    route = router.routes[("topic3", "sub3")]
    assert route.input_model is None
    assert route.output_model == OutputModel


def test_event_router_handler_no_models() -> None:
    router = EventRouter()

    @router.event_handler(topic="topic4", subscription="sub4")
    def handler(x: int) -> str:
        return "ok"

    route = router.routes[("topic4", "sub4")]
    assert route.input_model is None
    assert route.output_model is None


def test_event_router_multiple_routes() -> None:
    router = EventRouter()

    @router.event_handler(topic="a", subscription="s1")
    def handler1(x: InputModel) -> OutputModel:
        return OutputModel(baz="1")

    @router.event_handler(topic="b", subscription="s2")
    def handler2(x: InputModel) -> OutputModel:
        return OutputModel(baz="2")

    assert len(router.routes.keys()) == 2
    assert router.routes[("a", "s1")].topic == "a"
    assert router.routes[("b", "s2")].topic == "b"


def test_event_router_arguments_must_be_kwargs() -> None:
    router = EventRouter()

    with pytest.raises(TypeError) as e:

        @router.event_handler("a", "s1")  # type: ignore[misc]
        def handler1(x: InputModel) -> OutputModel:
            return OutputModel(baz="1")

    assert (
        e.value.args[0]
        == "EventRouter.event_handler() takes 1 positional argument but 3 were given"
    )


def test_conflicting_topics_and_subscriptions_raise_error() -> None:
    router = EventRouter()

    @router.event_handler(topic="a", subscription="s1")
    def handler1(x: InputModel) -> OutputModel:
        return OutputModel(baz="1")

    with pytest.raises(
        ValueError, match="Duplicate handler for topic 'a' and subscription 's1'"
    ):

        @router.event_handler(topic="a", subscription="s1")
        def handler2(x: InputModel) -> OutputModel:
            return OutputModel(baz="2")
