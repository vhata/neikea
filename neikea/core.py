import logging
import sys
from traceback import format_exception
from typing import List, Optional

import discord
import plugins
from plugins import core

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neikea")

PLUGINS = {
    "Time": core.Time,
    "Banter": core.Banter,
    "Strip": core.Strip,
    "Addressed": core.Addressed,
    "Ignore": core.Ignore,
}


class Event(dict):
    def __init__(self, type_: str, message: str, sender: discord.User):
        self.type: str = type_
        self.message: str = message
        self.sender: discord.User = sender
        self.processed: bool = False

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, name, value):
        self[name] = value


class Dispatcher(discord.Client):
    processors: List[plugins.Processor] = []

    def __init__(self):
        super().__init__()

        self.processors = []

    async def process(self, event: Event):
        for p in self.processors:
            await p.process(event)

    async def load_processors(self):
        self.processors = []
        for p in PLUGINS:
            processor = PLUGINS[p](p)
            await processor.setup(self)
            self.processors.append(processor)
        self.processors.sort(key=lambda x: x.priority)

    async def on_ready(self):
        logger.info("Connected as %s (id: %s)", self.user, self.user.id)
        for guild in self.guilds:
            logger.info(f"Connected to: %s (id: %s)", guild.name, guild.id)
        await self.load_processors()

    async def on_message(self, message):
        # Failsafe
        if message.author == self.user:
            return

        logger.info(f"<%s> %s", message.author, message.content)
        event = Event("message", message.content, message.author)
        event.discord_message = message
        await self.process(event)

    async def on_error(self, event, *args, **kwargs):
        logger.error("Error: %s, %s, %s", event, args, kwargs)
        etype, value, tb = sys.exc_info()
        logger.error("".join(format_exception(etype, value, tb)))
