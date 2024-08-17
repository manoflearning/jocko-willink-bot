import logging
from pathlib import Path
from typing import Optional
import discord
import json
from datetime import datetime, timedelta, timezone
from PIL import Image
from PIL.ExifTags import TAGS


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_date_from_image(image_path: str) -> Optional[str]:
    with Image.open(image_path) as img:
        exif_data = img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                if TAGS.get(tag_id, tag_id) == "DateTimeOriginal":
                    return value
    return None


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
        self.KST = timezone(timedelta(hours=9))

    async def on_ready(self):
        channel = self.get_channel(self.CHANNEL_ID)
        if channel and isinstance(
            channel, discord.TextChannel
        ):  # Ensure it's a text channel
            await channel.send(
                "Jocko Willink reporting for duty. Time to get after it."
            )

    async def on_message(self, message: discord.Message):
        if message.channel.id != self.CHANNEL_ID:
            return
        if message.author == self.user:
            return

        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.lower().endswith(("png", "jpg", "jpeg")):
                    # download the image
                    image_dir = Path(
                        f"./images/{datetime.now().strftime('%Y%m%d')}"
                    ).resolve()
                    image_dir.mkdir(parents=True, exist_ok=True)

                    image_path = f"./images/{datetime.now().strftime('%Y%m%d')}/{message.author.display_name}_{attachment.filename}"
                    await attachment.save(Path(image_path))

                    # Extract the date from image metadata
                    image_date_str = extract_date_from_image(image_path)
                    if image_date_str:
                        try:
                            image_date = datetime.strptime(
                                image_date_str, "%Y:%m:%d %H:%M:%S"
                            )
                            image_date = image_date.astimezone(self.KST)

                            if is_within_time_range(
                                image_date
                            ):  # successful wake-up confirmation
                                await message.add_reaction("💪")
                                await message.channel.send(
                                    f"{message.author.mention} Wake-up CONFIRMED. Discipline equals freedom. Well done."
                                )
                            else:  # photo taken outside the allowed time range
                                await message.add_reaction("🔴")
                                await message.channel.send(
                                    f"{message.author.mention} Wake-up FAILED. That photo wasn't taken between 07:30 and 08:30 KST. No shortcuts. No excuses."
                                )
                        except ValueError:
                            await message.add_reaction("⚠️")
                            await message.channel.send(
                                f"{message.author.mention} INVALID date format in EXIF data. Couldn't confirm the date. Step up."
                            )
                    else:  # invalid photo or missing metadata
                        await message.add_reaction("⚠️")
                        await message.channel.send(
                            f"{message.author.mention} INVALID photo. Couldn't confirm the date. Only legit submissions count. Step up."
                        )
                else:  # non-image file uploaded
                    await message.add_reaction("❌")
                    await message.channel.send(
                        f"{message.author.mention} UNACCEPTABLE. Only image files are allowed. Stick to the plan. No deviations."
                    )
        else:  # no image attached to the message
            await message.add_reaction("❗")
            await message.channel.send(
                f"{message.author.mention} INCOMPLETE submission. No image attached. Get it right. Now."
            )


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    bot = JockoWillinkBot(intents=intents)
    bot.run(bot.TOKEN)
