import logging
import random
import re
from datetime import datetime

from plugins import Processor, handler, match

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neikea.plugins")


class Strip(Processor):
    """
    Turn the 'message' string into a dict that will contain different
    versions of the message, including (after this module):
    'raw': the message as received
    'stripped': the message without leading/trailing whitespace and punctuation
    'clean': the same as 'stripped' at first, but will be replaced in the
             Addressed Processor if the bot has been addressed
    """

    priority = -1600

    pattern = re.compile(r"^\s*(.*?)\s*[?!.]*\s*$", re.DOTALL)

    @handler
    async def handle_strip(self, event):
        event.message = {
            "raw": event.message,
        }
        m = self.pattern.search(event.message["raw"])
        assert m is not None
        event.message["clean"] = event.message["stripped"] = m.group(1)


time_replies = ["It's %H:%M!", "It's %-I:%M %p!"]
date_replies = [
    "It's %A, %B %-d, %Y!",
    "According to my Gary Larson's Far Side desk calendar, it's %A, %B %-d, %Y!",
]


class Time(Processor):
    @match("time")
    async def time(self, event):
        t = datetime.now()
        await event.discord_message.channel.send(
            t.strftime(random.choice(time_replies))
        )
        event.processed = True

    @match("date")
    async def date(self, event):
        t = datetime.now()
        await event.discord_message.channel.send(
            t.strftime(random.choice(date_replies))
        )
        event.processed = True


greetings = (
    "afternoon",
    "bonjour",
    "buon giorno",
    "ello",
    "evening",
    "good day",
    "good morning",
    "hello",
    "hey",
    "heya",
    "hi there",
    "hi",
    "hiya",
    "hoe gaan dit",
    "hoe lyk it",
    "hoezit",
    "hola",
    "howdy",
    "howsit",
    "howzit",
    "lo",
    "llo",
    "morning",
    "salut",
    "sup",
    "wassup",
    "wasup",
    "what's up",
    "word",
    "wotcha",
    "wotcher",
    "wussup",
    "yo",
)
banter_replies = {
    "greet": {
        "matches": [
            r"\b("
            + "|".join(
                list(greetings) + [g.replace(" ", "") for g in greetings if " " in g]
            )
            + r")\b"
        ],
        "responses": greetings,
    },
    "reward": {
        "matches": [r"\bbot(\s+|\-)?snack\b"],
        "responses": ["thanks, $who", "$who: thankyou!", ":)"],
    },
    "praise": {
        "matches": [
            r"\bgood(\s+fuckin[\'g]?)?\s+(lad|bo(t|y)|g([ui]|r+)rl)\b",
            r"\byou\s+(rock|rocks|rewl|rule|are\s+so+\s+co+l)\b",
        ],
        "responses": ["thanks, $who", "$who: thankyou!", ":)"],
    },
    "thanks": {
        "matches": [r"\bthank(s|\s*you)\b", r"^\s*ta\s*$", r"^\s*shot\s*$"],
        "responses": [
            "no problem, $who",
            "$who: my pleasure",
            "sure thing, $who",
            "no worries, $who",
            "$who: np",
            "no probs, $who",
            "$who: no problemo",
            "$who: not at all",
        ],
    },
    "criticism": {
        "matches": [
            r"\b((kak|bad|st(u|oo)pid|dumb)(\s+fuckin[\'g]?)?\s+(bo(t|y)|g([ui]|r+)rl))|(bot(\s|\-)?s(mack|lap))\b",
        ],
        "responses": ["*whimper*", "sorry, $who :(", ":(", "*cringe*"],
    },
    "testdates": {
        "matches": [
            r"\binterpolate dates\b",
        ],
        "responses": [
            "year $year month2 $month2 month $month mon $mon day2 $day2 day $day date $date dow $dow weekday $weekday",
        ],
    },
    "testtimes": {
        "matches": [
            r"\binterpolate times\b",
        ],
        "responses": [
            "hour $hour minute $minute second $second time $time unixtime $unixtime",
        ],
    },
    "testdiscord": {
        "matches": [
            r"\binterpolate discord\b",
        ],
        "responses": ["who $who channel $channel server $server"],
    },
}


def _interpolate(message, event):
    "Expand factoid variables"
    utcnow = datetime.utcnow()
    now = datetime.now()

    substitutions = [
        ("who", f"<@!{event.discord_message.author.id}>"),
        ("channel", f"<#{event.discord_message.channel.id}>"),
        ("server", event.discord_message.guild.name),
        ("year", str(now.year)),
        ("month2", "%02i" % now.month),
        ("month1", str(now.month)),
        ("month", now.strftime("%B")),
        ("mon", now.strftime("%b")),
        ("day2", "%02i" % now.day),
        ("day", str(now.day)),
        ("hour", now.strftime("%-I")),
        ("hour24", str(now.hour)),
        ("minute", str(now.minute)),
        ("second", str(now.second)),
        ("date", now.strftime("%Y-%m-%d")),
        ("time", now.strftime("%-I:%M %p")),
        ("dow", now.strftime("%A")),
        ("weekday", now.strftime("%A")),
        ("unixtime", utcnow.strftime("%s")),
    ]

    for var, expansion in substitutions:
        message = message.replace("$" + var, expansion)
    return message


class Banter(Processor):
    @handler
    async def static(self, event):
        for banter in banter_replies.values():
            for match in banter["matches"]:
                if re.fullmatch(match, event.message["clean"], re.I):
                    await event.discord_message.channel.send(
                        _interpolate(random.choice(banter["responses"]), event)
                    )
                    event.processed = True
                    return
