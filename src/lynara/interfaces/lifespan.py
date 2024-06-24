import asyncio
import logging

from lynara.types import ASGIApp, LifespanMode, Message

LOGGER = logging.getLogger(__name__)


class LifespanInterface:
    def __init__(self, app: ASGIApp, lifespan_mode: LifespanMode) -> None:
        self.app = app
        self.lifespan_mode = lifespan_mode
        self.validate_mode()
        self.scope = {
            "type": "lifespan",
            "asgi": {"spec_version": "1.0", "version": "3.0"},
            "state": {},
        }
        self._queue: asyncio.Queue[Message] = asyncio.Queue()
        self._startup_event = asyncio.Event()
        self._shutdown_event = asyncio.Event()
        self.error_occured = False
        self.startup_failed = False
        self.shutdown_failed = False

    def validate_mode(self) -> None:
        if self.lifespan_mode == LifespanMode.OFF:
            raise Exception("Lifespan mode is off, but lifespan interface is used")

    async def __aenter__(self) -> "LifespanInterface":
        await self.startup()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.shutdown()

    async def startup(self) -> None:
        loop = asyncio.get_event_loop()
        main_lifespan_task = loop.create_task(self.main())
        await self._queue.put({"type": "lifespan.startup"})
        await self._startup_event.wait()

        if self.startup_failed or (
            self.error_occured and self.lifespan_mode == LifespanMode.ON
        ):
            LOGGER.error("Application startup failed. Exiting.")
            possible_exception = main_lifespan_task.exception()
            if isinstance(possible_exception, Exception):
                raise possible_exception

    async def shutdown(self):
        await self._queue.put({"type": "lifespan.shutdown"})
        LOGGER.debug("Waiting for shutdown")
        await self._shutdown_event.wait()
        LOGGER.debug("Shutdown complete")

    async def main(self):
        try:
            await self.app(scope=self.scope, receive=self.receive, send=self.send)
        except BaseException as exc:
            self.error_occured = True
            if self.lifespan_mode == LifespanMode.AUTO:
                LOGGER.info("Lifespan protocol appears to be unsupported, skipping.")
            else:
                LOGGER.exception(
                    "Error in lifespan interface, does the app support lifespan?"
                )
            raise exc
        finally:
            self._startup_event.set()
            self._shutdown_event.set()

    async def receive(self) -> Message:
        return await self._queue.get()

    async def send(self, message: Message) -> None:
        message_type = message["type"]
        if message_type == "lifespan.startup.complete":
            self._startup_event.set()
            return
        elif message_type == "lifespan.startup.failed":
            self.startup_failed = True
            self._startup_event.set()
            raise Exception(f'Startup failed {message.get("message", "")}')
        elif message_type == "lifespan.shutdown.complete":
            self._shutdown_event.set()
            return
        elif message_type == "lifespan.shutdown.failed":
            self.shutdown_failed = True
            self._shutdown_event.set()
            raise Exception(f'Shutdown failed {message.get("message", "")}')
        raise Exception(f"Invalid startup message type {message_type}")
