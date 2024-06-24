import logging
from contextlib import AsyncExitStack
from time import time

from lynara import LifespanInterface
from lynara.interfaces.base import HTTPInterface
from lynara.types import LifespanMode

LOGGER = logging.getLogger(__name__)


class Lynara:
    def __init__(self, app, lifespan_mode: LifespanMode = LifespanMode.AUTO):
        self.app = app
        self.lifespan_mode = lifespan_mode

    async def run(
        self,
        event,
        context,
        interface_class: type[HTTPInterface],
        base_path: str | None = None,
    ):
        start_time = time()
        interface = interface_class(
            app=self.app, event=event, context=context, base_path=base_path
        )
        async with AsyncExitStack() as stack:
            if self.lifespan_mode in (LifespanMode.ON, LifespanMode.AUTO):
                await stack.enter_async_context(
                    LifespanInterface(app=self.app, lifespan_mode=self.lifespan_mode)
                )
            interface_start_time = time()
            lambda_response = await interface()
        LOGGER.info(
            "Lynara execution time: %.5f s, out of which interface time: %.5f s",
            (time() - start_time),
            (time() - interface_start_time),
        )
        return lambda_response
