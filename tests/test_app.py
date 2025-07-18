from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

from fastevent import EventApp, EventRoute, EventRouter


@pytest.fixture
def fake_route():
    route = MagicMock(spec=EventRoute)
    route.topic = "test-topic"
    route.subscription = "test-sub"
    route.handle_message = AsyncMock()
    return route


@pytest.fixture
def fake_message():
    return MagicMock(name="ServiceBusMessage")


@pytest.fixture
def fake_router(fake_route):
    router = EventRouter()
    router.routes = {(fake_route.topic, fake_route.subscription): fake_route}
    return router


@pytest.fixture
def mock_sb_receiver():
    receiver = create_autospec(ServiceBusReceiver, instance=True)
    receiver.__aenter__.return_value = receiver
    receiver.__aiter__.return_value = iter([])
    receiver.complete_message = AsyncMock()
    return receiver


@pytest.fixture
def mock_sb_client(mock_sb_receiver):
    client = create_autospec(ServiceBusClient, instance=True)
    client.get_subscription_receiver.return_value = mock_sb_receiver
    return client


@pytest.fixture
def fake_route():
    route = MagicMock(spec=EventRoute)
    route.topic = "test-topic"
    route.subscription = "test-sub"
    route.handle_message = AsyncMock()
    return route


@pytest.mark.asyncio
async def test_include_router_registers_router(fake_router, mock_sb_client):
    app = EventApp(sb_client=mock_sb_client)
    assert len(app.routers) == 0
    app.include_router(fake_router)
    assert app.routers == [fake_router]


@pytest.mark.asyncio
async def test_app_run_invokes_get_subscription_receiver(
    fake_router, mock_sb_client, mock_sb_receiver
):
    app = EventApp(sb_client=mock_sb_client)
    app.include_router(fake_router)

    await app.run()

    mock_sb_client.get_subscription_receiver.assert_called_once_with(
        topic_name="test-topic",
        subscription_name="test-sub",
    )


@pytest.mark.asyncio
async def test_app_run_invokes_route_handle_message(
    fake_message, fake_router, fake_route, mock_sb_client
):
    # Simulate one message being received
    mock_receiver = create_autospec(ServiceBusReceiver, instance=True)
    mock_receiver.__aenter__.return_value = mock_receiver
    mock_receiver.__aiter__.return_value = iter([fake_message])
    mock_receiver.complete_message = AsyncMock()

    mock_sb_client.get_subscription_receiver.return_value = mock_receiver

    app = EventApp(sb_client=mock_sb_client)
    app.include_router(fake_router)

    await app.run()

    fake_route.handle_message.assert_awaited_once_with(fake_message)
    mock_receiver.complete_message.assert_awaited_once_with(fake_message)
