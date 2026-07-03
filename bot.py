import os
import re
import asyncio
from pathlib import Path
from datetime import datetime

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

DATA_DIR = Path("data")
STATE_FILE = Path("state.txt")

TIMEZONE = pytz.timezone("Asia/Kolkata")

# Change these if you ever want another posting time.
POST_HOUR = 19      # 7 PM IST
POST_MINUTE = 0

intents = discord.Intents.default()
client = discord.Client(intents=intents)

scheduler = AsyncIOScheduler(timezone=TIMEZONE)


def natural_key(path):
    name = path.stem.lower()
    parts = re.split(r"(\d+)", name)
    return [int(p) if p.isdigit() else p for p in parts]


def load_state():
    if not STATE_FILE.exists():
        return {}

    state = {}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                try:
                    state[k] = int(v)
                except ValueError:
                    state[k] = 0

    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        for k, v in sorted(state.items()):
            f.write(f"{k}={v}\n")


async def daily_post():
    print(f"Running scheduled post: {datetime.now(TIMEZONE)}")

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("Channel not found.")
        return

    state = load_state()

    categories = sorted(
        [p for p in DATA_DIR.iterdir() if p.is_dir()],
        key=lambda p: p.name.lower()
    )

    for category in categories:

        images = sorted(
            [
                x for x in category.iterdir()
                if x.suffix.lower() in (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".webp"
                )
            ],
            key=natural_key
        )

        if not images:
            continue

        current = state.get(category.name, 0)

        if current >= len(images):
            print(f"{category.name}: completed")
            continue

        pair = images[current:current + 2]

        files = [discord.File(str(img)) for img in pair]

        await channel.send(
            content=f"**{category.name}**",
            files=files
        )

        state[category.name] = current + len(pair)

        await asyncio.sleep(2)

    save_state(state)

    print("Posting complete.")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    if not scheduler.running:
        scheduler.add_job(
            daily_post,
            trigger="cron",
            hour=POST_HOUR,
            minute=POST_MINUTE,
            id="daily_post",
            replace_existing=True,
        )

        scheduler.start()

        print(
            f"Scheduler started. Daily posting at "
            f"{POST_HOUR:02d}:{POST_MINUTE:02d} IST."
        )


client.run(TOKEN)
