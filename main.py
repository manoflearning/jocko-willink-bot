import asyncio
import logging
from pathlib import Path
import discord
import json
from datetime import datetime, timedelta, timezone


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_within_time_range(dt: datetime):
    start_time = dt.replace(hour=7, minute=30, second=0, microsecond=0)
    end_time = dt.replace(hour=8, minute=30, second=0, microsecond=0)
    return start_time <= dt <= end_time


class JockoWillinkBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
        self.TOKEN = config["TOKEN"]
        self.CHANNEL_ID = int(config["CHANNEL_ID"])
        self.TIMEZONE = timezone(timedelta(hours=9))

    async def on_ready(self):
        self.loop.create_task(self.alarm_task())

    async def alarm_task(self):
        while True:
            now = datetime.now(self.TIMEZONE)
            if now.hour == 7 and now.minute == 30:
                channel = self.get_channel(self.CHANNEL_ID)
                if channel and isinstance(channel, discord.TextChannel):
                    await channel.send(
                        "🛎️ It's 07:30 KST! Time to rise and grind! Discipline equals freedom."
                    )
                await asyncio.sleep(300)
            else:
                await asyncio.sleep(1)

    async def on_message(self, message: discord.Message):
        if message.channel.id != self.CHANNEL_ID:
            return
        if message.author == self.user:
            return

        message_time = message.created_at.replace(tzinfo=timezone.utc).astimezone(
            self.TIMEZONE
        )
        if is_within_time_range(message_time):
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.lower().endswith(("png", "jpg", "jpeg")):
                        image_dir = Path(
                            f"./images/{datetime.now().strftime('%Y%m%d')}"
                        ).resolve()
                        image_dir.mkdir(parents=True, exist_ok=True)

                        image_path = f"./images/{datetime.now().strftime('%Y%m%d')}/{message.author.id}_{attachment.filename}"
                        await attachment.save(Path(image_path).resolve())

                        await message.add_reaction("💪")
                        await message.channel.send(
                            f"{message.author.mention} Wake-up CONFIRMED. Discipline equals freedom. Well done."
                        )
                    else:
                        await message.add_reaction("❌")
                        await message.channel.send(
                            f"{message.author.mention} UNACCEPTABLE. Only image files are allowed. Stick to the plan. No deviations."
                        )
            else:
                await message.add_reaction("❗")
                await message.channel.send(
                    f"{message.author.mention} INCOMPLETE submission. No image attached. Get it right. Now."
                )
        else:
            await message.add_reaction("🔴")
            await message.channel.send(
                f"{message.author.mention} Wake-up FAILED. That message wasn't sent between 07:30 and 08:30 KST. No shortcuts. No excuses."
            )


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    bot = JockoWillinkBot(intents=intents)
    bot.run(bot.TOKEN)
