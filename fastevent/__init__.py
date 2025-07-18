import asyncio
import functools
import inspect
import json
from collections.abc import Callable
from typing import Any, ParamSpec, Type, TypeVar, get_type_hints

from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient

from fastevent.router import EventRoute, EventRouter


class EventApp:
    def __init__(self, sb_client: ServiceBusClient) -> None:
        self.routers: list[EventRouter] = []
        self.sb_client: ServiceBusClient = sb_client

    def include_router(self, router: EventRouter):
        self.routers.append(router)

    async def run(self):
        async with self.sb_client:
            receivers = []
            for router in self.routers:
                for _, route in router.routes.items():
                    receiver = self.sb_client.get_subscription_receiver(
                        topic_name=route.topic,
                        subscription_name=route.subscription,
                    )
                    task = asyncio.create_task(self._run_receiver(route, receiver))
                    receivers.append(task)
            await asyncio.gather(*receivers)

    async def _run_receiver(self, route: EventRoute, receiver):
        async with receiver:
            async for message in receiver:
                await route.handle_message(message)
                await receiver.complete_message(message)
