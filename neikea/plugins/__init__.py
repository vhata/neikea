import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neikea.plugins")


class Processor(object):
    """Base class for plugins.
    Processors receive events and (optionally) do things with them.

    The following attributes affect how events are handled:

    event_types: Only these event types are handled
    priority: Processors are handled in ascending order of priority
    processed: Processor will handle events that other Processors have already
               marked as being dealt with
    """

    event_types = ("message",)
    priority = 1500  # middle ground
    processed = False

    def __init__(self, name):
        self.name = name

        self._event_handlers = []
        for n, item in type(self).__dict__.items():
            if getattr(item, "handler", False):
                self._event_handlers.append(item)

    async def process(self, event):
        "Process a single event"
        if event.type not in self.event_types:
            return

        if not self.processed and event.processed:
            return

        for method in self._event_handlers:
            found = False
            args = ()
            kwargs = {}
            if not hasattr(method, "pattern"):
                found = True
            elif hasattr(event, "message"):
                match = method.pattern.fullmatch(event.message)
                if match is not None:
                    found = True
                    args = match.groups()
                    kwargs = match.groupdict()
            if found:
                await method(self, event, *args, **kwargs)


def handler(function):
    "Wrapper: Handle all events"
    function.handler = True
    return function


def match(regex):
    "Wrapper: Handle all events where the message matches the regex"
    pattern = re.compile(regex, re.I | re.UNICODE | re.DOTALL)

    def wrap(function):
        function.handler = True
        function.pattern = pattern
        return function

    return wrap
