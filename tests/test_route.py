import pytest
from azure.servicebus import ServiceBusMessage
from pydantic import BaseModel

from fastevent import Route


class InputModel(BaseModel):
    foo: str
    bar: int


class OutputModel(BaseModel):
    baz: str


def test_route_with_input_and_output_models() -> None:
    def handler_with_models(input: InputModel) -> OutputModel:
        return OutputModel(baz="potato")

    route = Route("topic", "sub", handler_with_models)
    assert route.topic == "topic"
    assert route.subscription == "sub"
    assert route.handler == handler_with_models
    assert route.input_model is InputModel
    assert route.output_model is OutputModel


def test_route_with_input_model_only() -> None:
    def handler_with_input_only(input: InputModel):
        pass

    route = Route("topic", "sub", handler_with_input_only)
    assert route.input_model is InputModel
    assert route.output_model is None


def test_route_with_output_model_only() -> None:
    def handler_with_output_only() -> OutputModel:
        return OutputModel(baz="potato")

    route = Route("topic", "sub", handler_with_output_only)
    assert route.input_model is None
    assert route.output_model is OutputModel


def test_route_with_no_models() -> None:
    def handler_with_no_models(x: int) -> str:
        return "test"

    route = Route("topic", "sub", handler_with_no_models)
    assert route.input_model is None
    assert route.output_model is None


def test_route_equals() -> None:
    def simple_route(input: str) -> None:
        pass

    route = Route("topic", "sub", simple_route)
    assert route == Route("topic", "sub", simple_route)
    assert route != Route("topic", "sub2", simple_route)

    with pytest.raises(NotImplementedError):
        assert route == object


def test_route_hash() -> None:
    def simple_route(input: str) -> None:
        pass

    route = Route("topic", "sub", simple_route)
    assert hash(route)


@pytest.mark.asyncio
async def test_route_handle_message_success() -> None:
    def handler_with_models(input: InputModel) -> OutputModel:
        return OutputModel(baz="potato")

    route = Route("topic", "sub", handler_with_models)

    input_message = ServiceBusMessage(InputModel(foo="bar", bar=1).model_dump_json())
    processed_event = await route.handle_message(input_message)

    assert processed_event == '{"baz":"potato"}'
