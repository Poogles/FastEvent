import logging
import time

import pytest
from _pytest.logging import LogCaptureFixture
from azure.servicebus import ServiceBusClient as SyncServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient
from pydantic import BaseModel

from fastevent import EventApp, EventRouter
from tests.sb.emulator import AzureServiceBusEmulator

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def async_servicebus_client(servicebus: AzureServiceBusEmulator) -> ServiceBusClient:
    conn_str = servicebus.get_connection_string()

    client = ServiceBusClient.from_connection_string(conn_str, logging_enable=True)
    return client


class InputModel(BaseModel):
    foo: str
    bar: int


@pytest.mark.integration
def test_integration_success_message_processed(
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
        log.info("received an event: %r", message)
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


@pytest.mark.integration
def test_integration_success_message_sent_to_dql(
    servicebus_client: SyncServiceBusClient,
    async_servicebus_client: ServiceBusClient,
    topic: str,
    subscription: str,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    sender = servicebus_client.get_topic_sender(topic_name=topic)

    router = EventRouter()

    @router.event_handler(topic=topic, subscription=subscription)
    async def test(message: InputModel) -> None:
        log.info("received an event: %r", message)

    app = EventApp(sb_client=async_servicebus_client)
    app.include_router(router)

    app.run()

    payload = "test"

    # Confirm that the payload doesn't pass the check
    with pytest.raises(Exception):
        InputModel.model_validate_json(payload)

    sender.send_messages(ServiceBusMessage(payload))

    time.sleep(1)  # wait for service bus to do its thing.

    # Close any running asyncio tasks.
    app.stop()

    dead_letter_queue_path = f"{topic}/Subscriptions/{subscription}/$DeadLetterQueue"
    dlq_receiver = servicebus_client.get_queue_receiver(
        queue_name=dead_letter_queue_path,  # even though it's from a subscription
        max_wait_time=5,
    )
    with dlq_receiver:
        messages = dlq_receiver.receive_messages(max_message_count=10, max_wait_time=5)
        assert len(messages) == 1

        # Clear the DLQ to not effect any future tests.
        dlq_receiver.complete_message(messages[0])
