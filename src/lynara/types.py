from collections.abc import Awaitable, Callable, MutableMapping
from enum import Enum
from typing import Any

LambdaEvent = dict[str, Any]
Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class LifespanMode(str, Enum):
    AUTO = "auto"
    ON = "on"
    OFF = "off"
