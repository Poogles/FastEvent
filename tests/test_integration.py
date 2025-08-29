import logging
import time

import pytest
from _pytest.logging import LogCaptureFixture
from azure.servicebus import ServiceBusClient as SyncServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient

from fastevent import EventApp, EventRouter
from tests.sb.emulator import AzureServiceBusEmulator

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def async_servicebus_client(servicebus: AzureServiceBusEmulator) -> ServiceBusClient:
    conn_str = servicebus.get_connection_string()

    client = ServiceBusClient.from_connection_string(conn_str, logging_enable=True)
    return client


@pytest.mark.integration
def test_integration(
    servicebus_client: SyncServiceBusClient,
    async_servicebus_client: ServiceBusClient,
    topic: str,
    subscription: str,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    sender = servicebus_client.get_topic_sender(topic_name=topic)

    router = EventRouter()

    processed_events = []

    @router.event_handler(topic=topic, subscription=subscription)
    async def test(message: str) -> None:
        log.critical("received an event: %r", message)
        processed_events.append(message)

    app = EventApp(sb_client=async_servicebus_client)
    app.include_router(router)

    app.run()

    body = "test"
    sender.send_messages(ServiceBusMessage(body))

    time.sleep(1)  # wait for service bus to do its thing.

    assert processed_events == [body]

    # Close any running asyncio tasks.
    app.stop()
