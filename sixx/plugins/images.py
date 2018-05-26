from math import sqrt

import asks
import datetime
import numpy as np
import random
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageEnhance import Brightness
from PIL.ImageFont import truetype
from curio import spawn_thread
from curious.commands import Context, Plugin, command
from io import BytesIO

from sixx.plugins.utils.pillow import add_noise, add_scanlines, antialiased_text, save_image

SCANLINES, NOISE, BOTH = range(3)


class Images(Plugin):
    """
    Commands for image manipulation stuffs.
    """

    @command()
    async def vcr(self, ctx: Context, *, url: str):
        # TODO support attachments
        buffer = BytesIO()
        resp = await asks.get(url, stream=True)

        async for chunk in resp.body:
            buffer.write(chunk)

        async with ctx.channel.typing:
            async with spawn_thread():
                with Image.open(buffer) as image:
                    filter = np.random.choice(range(3), p=[0.7, 0.2, 0.1])

                    if filter == SCANLINES:
                        image = add_scanlines(image)
                    elif filter == NOISE:
                        image = add_noise(image)
                    else:
                        image = add_scanlines(image)
                        image = add_noise(image)

                    Brightness(image).enhance(2.5)

                    # hoo boy

                    text = np.random.choice(['PLAY', '  PAUSE'], p=[0.8, 0.2])
                    font = truetype('VCR_OSD_MONO.ttf', size=int(min(image.size) / 10))

                    start = datetime.datetime(1980, 1, 1, 0, 0)
                    now = datetime.datetime.utcnow()

                    # https://stackoverflow.com/a/8170651/7581432
                    random_date = start + datetime.timedelta(seconds=random.randint(0, int((now - start).total_seconds())))

                    topleft_text = antialiased_text(text, font, image.width, image.height, offset_x=1 / 30, offset_y=1 / 15)
                    image.paste(topleft_text, (0, 0), mask=topleft_text)

                    draw = Draw(image)
                    if text == 'PLAY':
                        width, height = font.getsize(text)
                        offset_x = width + image.width * (1 / 30) * 1.5
                        offset_y = image.height * (1 / 15)

                        draw.polygon(
                            [
                                (offset_x, offset_y),
                                (offset_x, offset_y + height),
                                (offset_x + sqrt(height ** 2 - (height / 2) ** 2), offset_y + height / 2)
                            ],
                            fill=(255, 255, 255)
                        )
                    else:
                        _, height = font.getsize('  ')
                        offset_x = image.width * (1 / 35)
                        offset_y = image.height * (1 / 15)

                        part = (height - offset_x / 2) / 8

                        draw.rectangle(
                            [(offset_x, offset_y + part), (offset_x + 3 * part, offset_y - part + height)],
                            fill=(255, 255, 255))
                        draw.rectangle(
                            [(offset_x + 5 * part, offset_y + part), (offset_x + 8 * part, offset_y - part + height)],
                            fill=(255, 255, 255))

                    # This is a nasty hack but oh well
                    time, date = random_date.strftime('%H:%M|%b. %d %Y').split('|')
                    wrap_width = len(date)
                    botleft_text = antialiased_text(time.ljust(wrap_width + 1) + date, font, image.width, image.height,
                                                    offset_x=1 / 35, offset_y=13 / 15, wrap_width=wrap_width)
                    image.paste(botleft_text, (0, 0), mask=botleft_text)

                    buffer = save_image(image, format=image.format)
        await ctx.channel.messages.upload(buffer, filename='shoutouts.' + image.format)
