import asyncio

from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

from fastevent.route import Route
from fastevent.router import EventRouter


class EventApp:
    def __init__(self, sb_client: ServiceBusClient) -> None:
        self.routers: list[EventRouter] = []
        self.sb_client: ServiceBusClient = sb_client

    def include_router(self, router: EventRouter):
        self.routers.append(router)

    async def run(self):
        breakpoint()
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

    async def _run_receiver(self, route: Route, receiver: ServiceBusReceiver) -> None:
        async with receiver:
            async for message in receiver:
                await route.handle_message(message)
                await receiver.complete_message(message)
