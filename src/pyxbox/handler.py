import asyncio
import signal
from typing import Any, Callable

from .event import Event
from .ports import EventProvider


class EventHandler:
    _handlers: dict[type[Event], Callable] = {}

    def __init__(self, event_provider: EventProvider) -> None:
        self._event_provider = event_provider
        self._original_signal_handlers: dict[int, Any] = {}
        self.running = False

    def _stop(self, sig: int = -1, frame: Any = None) -> None:
        self.running = False

    def register_signal_handlers(self) -> None:
        for signame in (signal.SIGINT, signal.SIGTERM):
            self._original_signal_handlers[signame] = signal.getsignal(signame)
            signal.signal(signame, self._stop)

    def unregister_signal_handlers(self) -> None:
        for signame, handler in self._original_signal_handlers.items():
            if handler is not None:
                signal.signal(signame, handler)

    @classmethod
    def on(cls, event_type: type[Event]) -> Callable:
        def handler(func: Callable) -> Callable:
            cls._handlers[event_type] = func
            return func

        # decorate method
        return handler

    async def _handle_next_event(self) -> None:
        async with self._event_provider.next() as event:
            if event is None:
                return
            print(f"Handling event: {event}")
            if type(event) in EventHandler._handlers:
                await EventHandler._handlers[type(event)](event)

    async def consume(self) -> None:
        print(f"Consuming events: {self._handlers}")
        self.running = True
        try:
            while self.running:
                await self._handle_next_event()
                await asyncio.sleep(0.01)
        except KeyboardInterrupt:
            self._stop()
