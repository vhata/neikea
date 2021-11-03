import logging
import sys
from traceback import format_exception
from typing import List, Optional

import discord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neikea")


class Dispatcher(discord.Client):
    async def on_ready(self):
        logger.info("Connected as %s (id: %s)", self.user, self.user.id)
        for guild in self.guilds:
            logger.info(f"Connected to: %s (id: %s)", guild.name, guild.id)

    async def on_message(self, message):
        # Failsafe
        if message.author == self.user:
            return

        logger.info(f"<%s> %s", message.author, message.content)

    async def on_error(self, event, *args, **kwargs):
        logger.error("Error: %s, %s, %s", event, args, kwargs)
        etype, value, tb = sys.exc_info()
        logger.error("".join(format_exception(etype, value, tb)))
