import logging
from collections.abc import Generator

import pytest

from tests.sb.emulator import AzureServiceBusEmulator

logger = logging.getLogger(__name__)


# Service Bus configuration.
NAMESPACE = "sbemulatorns"
TOPIC1 = "test-topic"
SUBSCRIPTION = "test-subscription"

SB_CONFIG = {
    "UserConfig": {
        "Namespaces": [
            {
                "Name": NAMESPACE,
                "Queues": [],
                "Topics": [
                    {
                        "Name": TOPIC1,
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
