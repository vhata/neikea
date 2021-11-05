import datetime
import random

from plugins import Processor, match

time_replies = ["It's %H:%M!", "It's %-I:%M %p!"]

date_replies = [
    "It's %A, %B %-d, %Y!",
    "According to my Gary Larson's Far Side desk calendar, it's %A, %B %-d, %Y!",
]


class Time(Processor):
    @match("time")
    async def time(self, event):
        t = datetime.datetime.now()
        await event.discord_message.channel.send(
            t.strftime(random.choice(time_replies))
        )
        event.processed = True

    @match("date")
    async def date(self, event):
        t = datetime.datetime.now()
        await event.discord_message.channel.send(
            t.strftime(random.choice(date_replies))
        )
        event.processed = True
