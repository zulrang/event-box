import importlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .datetime import utcnow


def _import_class(name: str) -> Any:
    """Import an class by name.

    Args:
        name (str): The name of the class to import.

    Returns:
        class: The imported class.

    Raises:
        ImportError: If the class cannot be imported.
    """
    module_name, class_name = name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    # metadata for external event bus
    _topic: str = ""
    _partition_key: str = "id"
    # metadata for event
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: datetime | None = Field(default=None)
    # pydantic config
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, use_enum_values=True)

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "topic": self._topic,
            "partition_key": self._partition_key,
            "class_name": str(self.get_fully_qualified_name()),
            "data": self.model_dump_json(by_alias=True),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def get_type(cls) -> str:
        return f"{cls.__module__}.{cls.__name__}"

    def get_fully_qualified_name(self) -> str:
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    @classmethod
    def from_data_store(cls, data: dict[str, Any]) -> "Event":
        event_class = _import_class(data["class_name"])
        event: Event = event_class(**json.loads(data["data"]))
        event.id = data["id"]
        return event

    def to_db(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Event) and self.id == other.id
