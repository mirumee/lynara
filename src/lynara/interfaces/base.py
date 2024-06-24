from abc import ABC, abstractmethod
from asyncio import Queue
from typing import Any

from lynara.types import ASGIApp, LambdaEvent, Message, Scope


class HTTPInterface(ABC):
    event: LambdaEvent
    context: Any
    is_response_completed: bool
    lambda_response: dict[str, Any]

    @classmethod
    @abstractmethod
    def match(cls, event: LambdaEvent) -> bool:
        raise NotImplementedError

    def __init__(
        self, app: ASGIApp, event: LambdaEvent, context, base_path: str | None = None
    ) -> None:
        self.app = app
        self.event = event
        self.context = context
        self.is_response_completed = False
        self._method: str | None = None
        self.lambda_response = {}
        self.app_queue: Queue[Message] = Queue()
        self.base_path = base_path

    async def __call__(self) -> Any:
        await self.app(self.scope, self.receive, self.send)
        return self.lambda_response

    @property
    @abstractmethod
    def scope(self) -> Scope:
        raise NotImplementedError

    @abstractmethod
    async def receive(self) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def send(self, message: Message) -> None:
        raise NotImplementedError
