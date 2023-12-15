
from .ports import Event, EventBus, EventStore


class TransactionalOutbox(EventBus):
    """
    Serializes and save or retrieves events from an EventRepository

    Transactional Outbox Pattern

    The transactional outbox pattern is a way to ensure that events are
    delivered to external systems in a reliable way. It is a pattern that
    is used in distributed systems to ensure that events are delivered
    exactly once to external systems.

    The pattern is implemented by having a separate table in the database
    that stores events that need to be sent to external systems. The
    events are stored in the outbox table in the same transaction as the
    rest of the data that is being saved. The events are then sent to
    external systems asynchronously. The events are sent to external
    systems by a separate process that polls the outbox table for new
    events. The events are sent to external systems in the same order
    that they were saved in the database. The events are sent to external
    systems exactly once. The events are sent to external systems in a
    transactional way. If the sending of an event fails, the event is
    retried.
    """

    def __init__(self, store: EventStore) -> None:
        self._store = store

    async def emit(self, event: Event) -> None:
        await self._store.save(event)
