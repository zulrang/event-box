from contextlib import asynccontextmanager
from typing import AsyncGenerator

from asyncpg.connection import Connection

from ..event import Event as EventModel
from ..ports import Event, EventSource


class PostgresEventSource(EventSource):
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    @asynccontextmanager
    async def start_transaction(self) -> AsyncGenerator[Connection, None]:
        """
        Start a transaction on the database.

        Args:
            None
        Returns:
            Connection: The connection to the database.
        """
        async with self._connection.transaction():
            yield self._connection

    async def pop(self) -> Event | None:
        """
        Pop an event from the database.

        Does not return an event that is currently being processed or locked.
        Locks the event so that it is not returned by another call to pop.
        Deletes the event from the database at the end of the transaction.

        Args:
            None
        Returns:
            Event: The event that was popped from the database.
        """
        row = await self._connection.fetchrow(
            """
            DELETE FROM events
            WHERE id = (
                SELECT id
                FROM events
                WHERE deleted_at IS NULL
                ORDER BY created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING *;
            """
        )
        if row:
            return EventModel.from_data_store(dict(row))
        else:
            return None
