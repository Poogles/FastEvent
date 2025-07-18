# FastEvent

FastEvent is a lightweight framework inspired by FastAPI but designed for
building event-driven applications.

It offers:

- Decorators to register handlers.
- Type hints + Pydantic models for message (de)serialisation and 
	validation.
- Pluggable clients for interacting with topics and subscriptions.
- Test Client for running tests against your handlers.

## Usage

```python
import logging
from pydantic import BaseModel
from azure.servicebus.aio import ServiceBusClient

from fastevent import EventApp, EventRouter

log = logging.getLogger(__name__)

async def notify_order(user_id: str, order_id: str) -> None:
	# Business logic here to notify of an order.
	pass


# Define your message schema
class OrderCreatedEvent(BaseModel):
    order_id: str
    user_id: str


# Set up your router and handler
router = EventRouter()

@router.event(topic="orders", subscription="order-created")
async def notify_order_created(event: OrderCreatedEvent) -> None:
    log.debug(
    	"Processing order: %r for user: %r", event.order_id, event.user_id
    )

    await notify_order(event.user_id, event.order_id)

# Create app and register router
sb_client = ServiceBusClient.from_connection_string("Endpoint=sb://...")
app = EventApp(sb_client)
app.include_router(router)

# Run the app (consumes messages)
import asyncio
asyncio.run(app.run())

```


## Installation

```bash
pip install fastevent
```


## TODO:

Before cutting a 0.1.0 release out of MVP.

- [ ] Integrated testing using the service bus emulator
- [ ] Support for other event sources.
- [ ] DI injection resolution using fastapi.Depends
- [ ] Add in base exception and use that.
- [ ] Fix key handling logic in routes/router.
- [ ] Add proper outbound event handling.
- [ ] Add validation that a `None` return type tagged event returns `None`
- [ ] Add in outbound topic configuration to decorator.
- [ ] Add support for types outside of pydantic?
