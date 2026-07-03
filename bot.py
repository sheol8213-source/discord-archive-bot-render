import os
import re
from pathlib import Path
import discord

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

DATA_DIR = Path("data")
STATE_FILE = Path("state.txt")

intents = discord.Intents.default()
client = discord.Client(intents=intents)


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
                state[k] = int(v)

    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        for k, v in sorted(state.items()):
            f.write(f"{k}={v}\n")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print("Channel not found")
        await client.close()
        return

    state = load_state()

    for category in sorted(DATA_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not category.is_dir():
            continue

        images = sorted(
            [
                x
                for x in category.iterdir()
                if x.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
            ],
            key=natural_key
        )

        if not images:
            continue

        current = state.get(category.name, 0)

        # Finished this category
        if current >= len(images):
            continue

        pair = images[current:current + 2]

        await channel.send(
            content=f"**{category.name}**",
            files=[discord.File(str(img)) for img in pair]
        )

        state[category.name] = current + len(pair)

    save_state(state)

    await client.close()


client.run(TOKEN)
