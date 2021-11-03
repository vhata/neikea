#!/usr/bin/env python
import os

from core import Dispatcher

TOKEN = os.getenv("DISCORD_TOKEN")

Dispatcher().run(TOKEN)
