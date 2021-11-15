import importlib
import inspect
import logging
import sys
from traceback import format_exception
from typing import List, Optional

import discord
import plugins

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neikea")

PLUGINS = ["core"]
LOAD = []
NOLOAD = []


class Event(dict):
    def __init__(self, type_: str, message: str, sender: discord.User):
        self.type: str = type_
        self.message: str = message
        self.sender: discord.User = sender
        self.processed: bool = False
        self.private: bool = False

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
            await self.load_processor(p)

    async def load_processor(self, name):
        module = "plugins." + name
        try:
            __import__(module)
            m = eval(module)
            importlib.reload(m)
        except Exception as e:
            logging.error("Couldn't load plugin '%s': %s", name, e)
            return

        for classname, klass in inspect.getmembers(m, inspect.isclass):
            if issubclass(klass, plugins.Processor) and klass != plugins.Processor:
                if f"{name}.{classname}" in NOLOAD:
                    logger.info("Skipping %s.%s due to NOLOAD", name, classname)
                    continue
                if not klass.autoload and f"{name}.{classname}" not in LOAD:
                    logger.info(
                        "Skipping %s.%s due to autoload being False", name, classname
                    )
                    continue
                logger.info("Loading Processor: %s.%s", name, classname)
                try:
                    processor = klass(classname)
                    await processor.setup(self)
                    self.processors.append(processor)
                except Exception as e:
                    logger.exception(
                        "Couldn't instantiate %s processor of %s plugin",
                        classname,
                        name,
                    )
                    continue
        # Sort this each time instead of in load_processors in case this method
        # is ever called from somewhere else
        self.processors.sort(key=lambda x: x.priority)
        logger.info("Loaded %s plugin", name)

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
        if isinstance(message.channel, discord.channel.DMChannel):
            event.private = True
        event.discord_message = message
        await self.process(event)

    async def on_error(self, event, *args, **kwargs):
        logger.error("Error: %s, %s, %s", event, args, kwargs)
        etype, value, tb = sys.exc_info()
        logger.error("".join(format_exception(etype, value, tb)))
