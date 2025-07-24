import functools
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from fastevent.route import Route

HandlerType = Callable[..., Any]


P = ParamSpec("P")
R = TypeVar("R")


class EventRouter:
    def __init__(self) -> None:
        self.routes: dict[tuple, Route] = dict()

    def event_handler(
        self, *, topic: str, subscription: str
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            if not callable(func):
                raise TypeError("event_handler must be applied to a callable.")

            route = Route(topic, subscription, func)
            # TODO: hash(route) might be better? Or a key creating helper?
            key = (topic, subscription)

            if self.routes.get(key):
                raise ValueError(
                    f"Duplicate handler for topic '{topic}' "
                    f"and subscription '{subscription}'"
                )

            self.routes[key] = route

            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                return func(*args, **kwargs)

            return wrapper

        return decorator
