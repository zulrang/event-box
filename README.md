# pyxbox

pyxbox is a Python library that provides basic implementations of the transactional outbox and inbox patterns using asyncpg.

## Installation

You can install pyxbox using pip:
```bash
$ pip install pyxbox
```

## Usage

### Emitting Events
`pyxbox` works by taking an existing PostgreSQL connection, which may or may not have an active transaction,
and dispatches subclasses of the `Event` class (which is a Pydantic data class) into the configurable `events` table
in the database.

The class allows for optional `_topic` and `_partition_key` fields which can be used in dispatching events to an
external event stream or queue.

```python
from pyxbox import Event, PostgresEventStore, TransactionalOutbox


class CustomEvent(Event):
    _topic: str = 'custom.event'
    _partition_key: str = 'id'
    event_data: dict = {}

async def do_stuff():
    connection = await asyncpg.connect('postgresql://test:testpass@localhost:5432/test')
    bus = TransactionalOutbox(PostgresEventStore(connection))

    async with connection.transaction():
        # do some database work
        bus.emit(CustomEvent(event_data={'foo': 'bar'}))
        # do more database work

```

### Processing Events

Events can then be processed either by sending the events to an external event stream, or by processing them directly
from the local database.

The first method is also wrapped in a transaction to ensure delivery of the event.  This should be run as an
independent background process or daemon, or within its own container.  Each loop is a separate transaction, and any
exceptions will ensure the event remains in the outbox.

```python
from pyxbox import Event, PostgresEventSource, TransactionalInbox


async def dispatch_events():
    connection = await asyncpg.connect('postgresql://test:testpass@localhost:5432/test')
    inbox = TransactionalInbox(PostgresEventSource(connection))

    for event in inbox.next():
        if event:
            # dispatch event to Kafka, Kinesis, SQS, etc.
            # require ack to ensure delivery
            external_bus.emit(event._topic, event._partition_key, event.model_dump())
        else:
            asyncio.sleep(1)
```

Another method is to handle events directly in the local code base.  The included EventHandler can assist with this.

```python
from pyxbox import Event, EventHandler


@EventHandler.on(CustomEvent)
async def handle_event(event: CustomEvent):
    # do something with event

async def main():
    connection = await asyncpg.connect('postgresql://test:testpass@localhost:5432/test')
    event_handler = EventHandler(PostgresEventSource(connection))

    await event_handler.consume()
```

The `consume()` method blocks until a `SIGINT`, `SIGTERM`, or `KeyboardInterrupt` and dispatches events to any functions
that are bound to the `EventHandler`, again within a transaction that will rollback upon exceptions.
