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
    addressed: Processor will only handle the event if the bot is addressed
    """

    event_types = ("message",)
    priority = 1500  # middle ground
    processed = False
    addressed = True

    def __init__(self, name):
        self.name = name

        self._event_handlers = []
        for n, item in type(self).__dict__.items():
            if getattr(item, "handler", False):
                self._event_handlers.append(item)

    async def setup(self, client):
        pass

    async def process(self, event):
        "Process a single event"
        if self.event_types and event.type not in self.event_types:
            return

        if not self.processed and event.processed:
            return

        if not event.get("addressed", True) and self.addressed:
            return

        for method in self._event_handlers:
            found = False
            args = ()
            kwargs = {}
            if not hasattr(method, "pattern"):
                found = True
            elif hasattr(event, "message"):
                message = event.message
                if isinstance(message, dict):
                    message = message[method.message_version]
                match = method.pattern.fullmatch(message)
                if match is not None:
                    found = True
                    args = match.groups()
                    kwargs = match.groupdict()
            if found:
                await method(self, event, *args, **kwargs)


def handler(function):
    "Wrapper: Handle all events"
    function.handler = True
    function.message_version = "clean"
    return function


def match(regex, version="clean"):
    "Wrapper: Handle all events where the message matches the regex"
    pattern = re.compile(regex, re.I | re.UNICODE | re.DOTALL)

    def wrap(function):
        function.handler = True
        function.pattern = pattern
        function.message_version = "clean"
        return function

    return wrap
