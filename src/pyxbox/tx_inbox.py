from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .ports import Event, EventSource, EventProvider


class TransactionalInbox(EventProvider):
    """
    A Transactional Inbox is a way to ensure that events are delivered to
    internal systems in a reliable way. It is a pattern that is used in
    distributed systems to ensure that events are delivered exactly once
    to internal systems.

    The pattern is implemented by having a separate table in the database
    that stores events that need to be sent to internal systems. The
    events are stored in the inbox table in the same transaction in which
    they are processed.

    The event is removed from the table at the end of the successful transaction.
    Rollback occurs if the transaction fails with an exception.

    Example:
    >>> inbox = TransactionalInbox(PostgresEventSource())
    >>> async with inbox.next() as event:
    >>>     print(event)
    """

    def __init__(self, source: EventSource) -> None:
        self.source = source

    @asynccontextmanager
    async def next(self) -> AsyncGenerator[Event | None, None]:
        """
        Generator to use used in a for loop to get the next event from the
        inbox.  Wraps the transaction.
        """
        async with self.source.start_transaction():
            event = await self.source.pop()
            yield event
