import asyncio
import logging
from threading import Thread

from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

from fastevent.route import Route
from fastevent.router import EventRouter

log = logging.getLogger(__name__)


class EventApp:
    def __init__(self, sb_client: ServiceBusClient) -> None:
        self.routers: list[EventRouter] = []
        self.sb_client: ServiceBusClient = sb_client
        self._running_thread: None | Thread = None
        self._receivers: list[asyncio.Task] = []

    def include_router(self, router: EventRouter):
        self.routers.append(router)

    def run(self) -> bool:
        log.info("Starting fastevent...")

        async def _start() -> None:
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

                self._receivers = receivers
                log.info("Started receivers and running.")
                try:
                    await asyncio.gather(*receivers)
                except asyncio.exceptions.CancelledError:
                    pass

        def run():
            asyncio.run(_start())

        self._running_thread = Thread(target=run)
        self._running_thread.start()

        return True

    def stop(self) -> bool:
        if not self._running_thread:
            raise Exception("Not a running app?")

        log.info("Stopping receiving.")
        for receiver in self._receivers:
            log.debug("Canceling task %r", receiver)
            receiver.cancel()

        self._running_thread.join()
        return True

    async def _run_receiver(self, route: Route, receiver: ServiceBusReceiver) -> None:
        log.debug("Starting receiver")
        async with receiver:
            log.debug("Starting receiving of messages...")
            async for message in receiver:
                log.debug("Received message: %r", message)
                await route.handle_message(message)
                log.debug("Handled message: %r", message)
                await receiver.complete_message(message)
                log.debug("Completed message: %r", message)
