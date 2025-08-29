import logging
from collections.abc import Generator

import pytest
from azure.servicebus import ServiceBusClient

from tests.sb.emulator import AzureServiceBusEmulator

logger = logging.getLogger(__name__)


# Service Bus configuration.
NAMESPACE = "sbemulatorns"
TOPIC = "test-topic"
SUBSCRIPTION = "test-subscription"

SB_CONFIG = {
    "UserConfig": {
        "Namespaces": [
            {
                "Name": NAMESPACE,
                "Queues": [],
                "Topics": [
                    {
                        "Name": TOPIC,
                        "Properties": {
                            "DefaultMessageTimeToLive": "PT1H",
                            "DuplicateDetectionHistoryTimeWindow": "PT20S",
                            "RequiresDuplicateDetection": False,
                        },
                        "Subscriptions": [
                            {
                                "Name": SUBSCRIPTION,
                                "Properties": {
                                    "DeadLetteringOnMessageExpiration": False,
                                    "DefaultMessageTimeToLive": "PT1H",
                                    "LockDuration": "PT1M",
                                    "MaxDeliveryCount": 10,
                                    "ForwardDeadLetteredMessagesTo": "",
                                    "ForwardTo": "",
                                    "RequiresSession": False,
                                },
                                "Rules": [],
                            },
                        ],
                    },
                ],
            }
        ],
        "Logging": {"Type": "File"},
    }
}


@pytest.fixture(scope="session")
def servicebus() -> Generator[AzureServiceBusEmulator]:
    sb = AzureServiceBusEmulator(config=SB_CONFIG)
    sb.start()

    yield sb


@pytest.fixture(scope="session")
def servicebus_client(servicebus: AzureServiceBusEmulator) -> ServiceBusClient:
    conn_str = servicebus.get_connection_string()

    client = ServiceBusClient.from_connection_string(conn_str, logging_enable=True)
    return client


@pytest.fixture
def topic() -> str:
    return TOPIC


@pytest.fixture
def subscription() -> str:
    return SUBSCRIPTION


@pytest.fixture(scope="session")
def async_servicebus_client(servicebus: AzureServiceBusEmulator) -> ServiceBusClient:
    conn_str = servicebus.get_connection_string()

    client = ServiceBusClient.from_connection_string(conn_str, logging_enable=True)
    return client
