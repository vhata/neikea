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

    async def process(self, event):
        "Process a single event"
        pass
