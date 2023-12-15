from typing import Any, AsyncContextManager, Callable, Protocol, TypeAlias
from uuid import UUID


class Event(Protocol):
    _topic: str
    _partition_key: str
    id: UUID

    def __str__(self) -> str:
        ...

    def model_dump(self) -> dict[str, Any]:
        ...

    def json(self) -> str:
        ...

    def serialize(self) -> dict[str, Any]:
        ...

    @classmethod
    def get_type(cls) -> str:
        ...

    @classmethod
    def from_data_store(cls, data: dict[str, Any]) -> "Event":
        ...


class EventBus(Protocol):
    """

    """
    async def emit(self, event: Event) -> None:
        ...


EventHandler: TypeAlias = Callable[..., Any]


class EventConsumer(Protocol):
    def register_handler(self, event_type: type[Event], handler: EventHandler) -> None:
        ...

    def unregister_handler(self, event_type: type[Event], handler: EventHandler) -> None:
        ...

    async def consume(self) -> None:
        ...

    def close(self) -> None:
        ...


class EventStore(Protocol):
    async def save(self, event: Event) -> None:
        ...


class EventSource(Protocol):

    def start_transaction(self) -> AsyncContextManager:
        ...

    async def pop(self) -> Event | None:
        ...



class EventProvider(Protocol):
    source: EventSource

    def next(self) -> AsyncContextManager[Event | None]:
        ...
