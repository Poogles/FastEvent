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
