import asyncio
import logging
from pathlib import Path
from typing import Tuple
import discord
from discord.ext import commands
import json
from datetime import datetime, timedelta, timezone


# logging
logging.basicConfig(level=logging.INFO)

# constants
KST = timezone(timedelta(hours=9))

config = {
    "TOKEN": "YOUR_BOT_TOKEN",
    "WAKEUP_CHANNEL_ID": "YOUR_WAKEUP_CHANNEL_ID",
}

with open("config.json", "r") as config_file:
    config = json.load(config_file)


# utility functions
def is_within_time_range(dt: datetime) -> bool:
    start_time = dt.replace(hour=7, minute=30, second=0, microsecond=0)
    end_time = dt.replace(hour=8, minute=30, second=0, microsecond=0)
    return start_time <= dt <= end_time


def wakeup_channel_id() -> int:
    return int(config["WAKEUP_CHANNEL_ID"])


# discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    if bot.user:
        logging.info(f"logged in as {bot.user.name}")
    bot.loop.create_task(wakeup_duration_alart())


@bot.command()
async def status(ctx: commands.Context, args: str):
    assert len(args) == 2


# wakeup verification
@bot.event
async def wakeup_duration_alart():
    while True:
        now = datetime.now(KST)
        if now.hour == 7 and now.minute == 30:
            channel = bot.get_channel(wakeup_channel_id())
            if channel and isinstance(channel, discord.TextChannel):
                await channel.send(
                    "🛎️ It's 07:30 KST! Time to rise and grind! The early hours are where success begins."
                )
                logging.info("07:30 KST alart")
            await asyncio.sleep(300)
        elif now.hour == 8 and now.minute == 30:
            channel = bot.get_channel(wakeup_channel_id())
            if channel and isinstance(channel, discord.TextChannel):
                await channel.send(
                    "🛎️ It's 08:30 KST! Time to wrap up the wake-up verification."
                )
                logging.info("08:30 KST alart")

            await asyncio.sleep(300)
        else:
            await asyncio.sleep(1)


@bot.command()
async def wakeup(ctx: commands.Context):
    if ctx.channel.id != wakeup_channel_id():
        logging.info(f"command not allowed in this channel: {ctx.channel.id}")
        logging.info(f"{ctx.channel.id}, {wakeup_channel_id()}")
        return

    if is_within_time_range(
        ctx.message.created_at.replace(tzinfo=timezone.utc).astimezone(KST)
    ):
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if attachment.filename.lower().endswith(("png", "jpg", "jpeg")):
                    image_dir = Path(
                        f"./images/{datetime.now().strftime('%Y%m%d')}"
                    ).resolve()
                    image_dir.mkdir(parents=True, exist_ok=True)

                    image_path = f"./images/{datetime.now().strftime('%Y-%m-%d')}/{ctx.message.author.id}_{attachment.filename}"
                    await attachment.save(Path(image_path).resolve())

                    await ctx.message.add_reaction("💪")
                    await ctx.message.channel.send(
                        f"{ctx.message.author.mention} Wake-up CONFIRMED. Discipline equals freedom. Well done."
                    )
                else:
                    await ctx.message.add_reaction("❌")
                    await ctx.message.channel.send(
                        f"{ctx.message.author.mention} UNACCEPTABLE. Only image files are allowed. Stick to the plan. No deviations."
                    )
        else:
            await ctx.message.add_reaction("❗")
            await ctx.message.channel.send(
                f"{ctx.message.author.mention} INCOMPLETE submission. No image attached. Get it right. Now."
            )
    else:
        await ctx.message.add_reaction("🔴")
        await ctx.message.channel.send(
            f"{ctx.message.author.mention} Wake-up FAILED. That message wasn't sent between 07:30 and 08:30 KST. No shortcuts. No excuses."
        )


# start the bot
bot.run(config["TOKEN"])
