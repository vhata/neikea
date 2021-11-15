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
    addressed = False

    pattern = re.compile(r"^\s*(.*?)\s*[?!.]*\s*$", re.DOTALL)

    @handler
    async def handle_strip(self, event):
        event.message = {
            "raw": event.message,
        }
        m = self.pattern.search(event.message["raw"])
        assert m is not None
        event.message["clean"] = event.message["stripped"] = m.group(1)


class Addressed(Processor):
    """
    Check to see if this event was addressed to the bot. It looks for messages
    of the forms:

    @botname: foo
    foo, @botname

    while still being lenient with whitespace and punctuation.  It avoids
    responding to messages like "@botname is here".
    After this processor, the event has a truthy "addressed" property, and
    the message has two new versions:
    'clean':
        the message stripped of the address and of punctuation (should be
        ready to be processed by most other processors)
    'deaddressed':
        the 'raw' message (with whitespace and punctuation) but without the
        address part of the message
    """

    priority = -1500
    addressed = False

    verbs = [
        "is",
        "has",
        "was",
        "might",
        "may",
        "would",
        "will",
        "isn't",
        "hasn't",
        "wasn't",
        "wouldn't",
        "won't",
        "can",
        "can't",
        "did",
        "didn't",
        "said",
        "says",
        "should",
        "shouldn't",
        "does",
        "doesn't",
    ]

    async def setup(self, client):
        self.mention = f"<@!{client.user.id}>"

        self.patterns = [
            re.compile(
                r"^\s*(?P<username>%s)" % self.mention
                + r"(?:\s*[:;.?>!,-]+\s+|\s+|\s*[,:]\s*)(?P<body>.*)",
                re.I | re.DOTALL,
            ),
            # "hello there, bot"-style addressing. But we want to be sure that
            # there wasn't normal addressing too.
            # (e.g. "@otheruser: we already have a bot, @botname")
            re.compile(
                r"^(?:\S+:.*|(?P<body>.*),\s*(?P<username>%s))[\s?!.]*$" % self.mention,
                re.I | re.DOTALL,
            ),
        ]
        # Avoid responding to things like "@botname is our bot"
        verbs = r"|".join(re.escape(x) for x in self.verbs)
        self.verb_pattern = re.compile(
            r"^(?:%s)\s+(?:%s)\s+" % (self.mention, verbs), re.I | re.DOTALL
        )

    @handler
    async def handle_addressed(self, event):
        if "addressed" not in event:
            event.addressed = False

        if self.verb_pattern.match(event.message["stripped"]):
            return

        # Private messages are always addressing the bot, although we will
        # still create the 'clean' version of the message below.
        if event.private:
            event.addressed = True

        for pattern in self.patterns:

            matches = pattern.search(event.message["stripped"])
            if matches and matches.group("username"):
                new_message = matches.group("body")
                event.addressed = True
                event.message["clean"] = new_message

                m = pattern.search(event.message["raw"])
                assert m is not None
                event.message["deaddressed"] = m.group("body")


class Ignore(Processor):
    priority = -1500
    addressed = False
    event_types = ()

    ignore_users = []

    @handler
    async def handle_ignore(self, event):
        if event.discord_message.author.id in self.ignore_users:
            logger.info("Ignoring %s", event.discord_message.author)
            event.processed = True


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
