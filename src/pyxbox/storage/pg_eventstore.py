from asyncpg.connection import Connection

from ..ports import Event, EventStore


class PostgresEventStore(EventStore):

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def save(self, event: Event) -> None:
        """
        Save an event to the database.

        Args:
            event (Event): The event to save.
        Returns:
            None
        """
        event_dict = event.serialize()
        await self._connection.execute(
            """
            INSERT INTO events (id, topic, partition_key, class_name, data, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            event_dict["id"],
            event_dict["topic"],
            event_dict["partition_key"],
            event_dict["class_name"],
            event_dict["data"],
            event_dict["created_at"],
            event_dict["updated_at"],
        )
