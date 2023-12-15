from datetime import datetime
from uuid import UUID, uuid4

import asyncpg
from pydantic import Field, BaseModel
import pytest
from asyncpg.connection import Connection

from pyxbox import Event, PostgresEventSource, PostgresEventStore, TransactionalInbox, TransactionalOutbox
from pyxbox.datetime import utcnow


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str
    created_at: datetime = Field(default_factory=utcnow)


class UserCreated(Event):
    _topic = "user.created"
    _partition_key = "user_id"
    user: User


@pytest.fixture
async def connection():
    conn = await asyncpg.connect('postgresql://pgxbox:testpass@localhost:5432/pgxbox')
    await conn.execute("DROP TABLE IF EXISTS users")
    await conn.execute("DELETE FROM events")
    await conn.execute("CREATE TABLE users (id UUID PRIMARY KEY, name TEXT, email TEXT, created_at TIMESTAMP)")
    yield conn
    await conn.execute("DROP TABLE IF EXISTS users")
    await conn.execute("DELETE FROM events")


async def test_end_to_end(connection: Connection):
    inbox = TransactionalInbox(PostgresEventSource(connection))
    outbox = TransactionalOutbox(PostgresEventStore(connection))

    # Emit an event
    user = User(name="Test User", email="test@gmail.com")
    await connection.execute("INSERT INTO users (id, name, email, created_at) VALUES ($1, $2, $3, $4)", user.id, user.name, user.email, user.created_at)
    await outbox.emit(UserCreated(user=user))

    # Process the event
    async with inbox.next() as event:
        assert event and isinstance(event, UserCreated)
        assert event._topic == "user.created"
        assert event.user.name == "Test User"
        assert event.user.email == "test@gmail.com"

    # Process the event
    async with inbox.next() as event:
        assert event is None


async def test_end_to_end_with_locking(connection: Connection):
    inbox = TransactionalInbox(PostgresEventSource(connection))
    outbox = TransactionalOutbox(PostgresEventStore(connection))

    # Emit 2 events
    user1 = User(name="Test User 1", email="test1@gmail.com")
    await connection.execute("INSERT INTO users (id, name, email, created_at) VALUES ($1, $2, $3, $4)", user1.id, user1.name, user1.email, user1.created_at)
    event1 = UserCreated(user=user1)
    await outbox.emit(event1)

    user2 = User(name="Test User 2", email="test2@gmail.com")
    await connection.execute("INSERT INTO users (id, name, email, created_at) VALUES ($1, $2, $3, $4)", user2.id, user2.name, user2.email, user2.created_at)
    event2 = UserCreated(user=user2)
    await outbox.emit(event2)

    # Process the event
    async with inbox.next() as event:
        assert event and isinstance(event, UserCreated)
        assert event._topic == "user.created"
        assert event.user.name == user1.name
        assert event.user.email == user1.email

        # Within current transaction, get the next event
        # the first event should be locked as it hasn't been ack'd
        async with inbox.next() as event:
            assert event and isinstance(event, UserCreated)
            assert event._topic == "user.created"
            assert event.user.name == user2.name
            assert event.user.email == user2.email

    # Process the event
    async with inbox.next() as event:
        assert event is None
