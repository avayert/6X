import asks
import numpy as np
from PIL import Image
from PIL.ImageEnhance import Brightness
from PIL.ImageFont import truetype
from curious.commands import Context, Plugin, command
from io import BytesIO

from sixx.plugins.utils.pillow import add_noise, add_scanlines, save_image

SCANLINES, NOISE, BOTH = range(3)


class Images(Plugin):
    """
    Commands for image manipulation stuffs.
    """

    @command()
    async def gett(self, ctx: Context, *, url: str):
        # TODO support attachments
        buffer = BytesIO()
        resp = await asks.get(url, stream=True)

        async for chunk in resp.body:
            buffer.write(chunk)

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

            buffer = save_image(image, format=image.format)
            await ctx.channel.messages.upload(buffer, filename='shoutouts.' + image.format)
