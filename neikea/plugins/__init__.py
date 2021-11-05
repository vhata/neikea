import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neikea.plugins")


class Processor(object):
    """Base class for plugins.
    Processors receive events and (optionally) do things with them.
    """

    def __init__(self, name):
        self.name = name

        self._event_handlers = []
        for n, item in type(self).__dict__.items():
            if getattr(item, "handler", False):
                self._event_handlers.append(item)

    async def process(self, event):
        "Process a single event"
        pass


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
