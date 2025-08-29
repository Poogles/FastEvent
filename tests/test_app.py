import logging
import time
from collections.abc import Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

from fastevent import EventApp, EventRouter, Route

log = logging.getLogger(__name__)


@pytest.fixture
def empty_route() -> Route:
    def test(arg: Any) -> None:
        pass

    route = Route(topic="test-topic", subscription="test-sub", handler=test)
    return route


@pytest.fixture
def fake_route() -> Route:
    route = MagicMock(spec=Route)
    route.topic = "test-topic"
    route.subscription = "test-sub"
    route.handle_message = AsyncMock()
    return route


@pytest.fixture
def fake_message() -> ServiceBusMessage:
    return MagicMock(name="ServiceBusMessage", spec=ServiceBusMessage)


@pytest.fixture
def fake_router(fake_route: Route) -> EventRouter:
    router = EventRouter()
    # Stub the empty route in directly.
    router.routes = {(fake_route.topic, fake_route.subscription): fake_route}
    return router


@pytest.fixture
def mock_sb_client() -> ServiceBusClient:
    client = create_autospec(ServiceBusClient, instance=True)
    return client


@pytest.mark.asyncio
async def test_include_router_registers_router(
    fake_router: EventRouter, mock_sb_client: ServiceBusClient
):
    app = EventApp(sb_client=mock_sb_client)
    assert len(app.routers) == 0
    app.include_router(fake_router)
    assert app.routers == [fake_router]


@pytest.mark.asyncio
async def test_app_run_invokes_get_subscription_receiver(
    fake_router: EventRouter,
    mock_sb_client: ServiceBusClient,
):
    app = EventApp(sb_client=mock_sb_client)
    app.include_router(fake_router)

    app.run()

    time.sleep(0.1)  # required because this happens in a thread

    mock_sb_client.get_subscription_receiver.assert_called_once_with(  # type: ignore
        topic_name="test-topic",
        subscription_name="test-sub",
    )


@pytest.fixture
def mock_receiver() -> Callable[[ServiceBusMessage], ServiceBusReceiver]:
    def _receiver(fake_message: ServiceBusMessage):
        mock_receiver = create_autospec(ServiceBusReceiver, instance=True)
        mock_receiver.__aenter__.return_value = mock_receiver
        mock_receiver.__aiter__.return_value = iter([fake_message])
        mock_receiver.complete_message = AsyncMock()
        return mock_receiver

    return _receiver


@pytest.mark.asyncio
async def test_app_run_invokes_route_handle_message(
    mocker,
    fake_message: ServiceBusMessage,
    mock_sb_client: ServiceBusClient,
    mock_receiver: Callable[[Any], ServiceBusReceiver],
) -> None:
    _receiver = mock_receiver(fake_message)
    mock_sb_client.get_subscription_receiver.return_value = _receiver  # type: ignore

    router = EventRouter()

    @router.event_handler(topic="test-topic", subscription="test-sub")
    def test(arg: Any) -> None:
        pass

    mock_handle_message = mocker.spy(
        router.routes[("test-topic", "test-sub")], "handle_message"
    )

    app = EventApp(sb_client=mock_sb_client)
    app.include_router(router)

    app.run()

    time.sleep(0.1)  # required because this happens in a thread

    mock_handle_message.assert_awaited_once_with(fake_message)
    _receiver.complete_message.assert_awaited_once_with(fake_message)  # type: ignore


def test_app_stop_no_running_app(
    mock_sb_client: ServiceBusClient,
) -> None:
    app = EventApp(sb_client=mock_sb_client)

    with pytest.raises(Exception):
        # No app is running, so stopping is unavailable.
        app.stop()
