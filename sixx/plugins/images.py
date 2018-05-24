import asks
from PIL import Image
from PIL.ImageDraw import Draw
from curious.commands import Context, Plugin, command
from io import BytesIO

from sixx.plugins.utils.pillow import save_image


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
            with Image.new('RGBA', image.size) as img:
                draw = Draw(img, mode='RGBA')

                for y in range(image.height):
                    if y % 2 == 0:
                        colour = 0, 0, 0, 50
                    else:
                        colour = 255, 255, 255, 50

                    draw.rectangle([(0, y), (image.width, y + 1)], fill=colour)
                image.paste(img, (0, 0), img)

            buffer = save_image(image, format='jpeg')
            await ctx.channel.messages.upload(buffer, filename='shoutouts.jpeg')
