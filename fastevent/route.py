import inspect
import json
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, get_type_hints

from azure.servicebus import ServiceBusMessage
from pydantic import BaseModel, ValidationError

HandlerType = Callable[..., Any]


P = ParamSpec("P")
R = TypeVar("R")


class Route:
    def __init__(self, topic: str, subscription: str, handler: HandlerType):
        self.topic = topic
        self.subscription = subscription
        self.handler = handler
        self.input_model = self._resolve_input_model()
        self.output_model = self._resolve_output_model()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Route):
            raise NotImplementedError()
        return (self.topic, self.subscription) == (other.topic, other.subscription)

    def __hash__(self) -> int:
        return hash((self.topic, self.subscription))

    def _resolve_input_model(self) -> type[BaseModel] | None:
        sig = inspect.signature(self.handler)
        for param in sig.parameters.values():
            if issubclass(param.annotation, BaseModel):
                return param.annotation
        return None

    def _resolve_output_model(self) -> type[BaseModel] | None:
        return_type = get_type_hints(self.handler).get("return")
        if return_type and issubclass(return_type, BaseModel):
            return return_type
        return None

    async def handle_message(self, raw_message: ServiceBusMessage) -> str | None:
        """Deserialize the message, call the handler, serialize the output."""
        try:
            # TODO: This isn't how service bus works.
            body = str(raw_message)
            data = json.loads(body)

            # Deserialize input
            input_obj = self.input_model(**data) if self.input_model else None

            # Call handler
            result = await self._maybe_async(self.handler, input_obj)

            # TODO: This is a mess.
            if self.output_model and result is not None:
                return self.output_model.parse_obj(result).json()

        except ValidationError:
            # TODO: Do something here
            ...
        except Exception:
            # TODO: Do something generic here?
            ...

        return None

    async def _maybe_async(self, func: Callable, *args):
        if inspect.iscoroutinefunction(func):
            return await func(*args)
        return func(*args)
