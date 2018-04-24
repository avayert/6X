from curio import async_thread
from curious.commands import Context, Plugin, command
from io import BytesIO
from wand.color import Color
from wand.image import Image

from sixx.plugins.utils import Colour


class Colours(Plugin):
    """
    Colour related commands.
    """

    @staticmethod
    @async_thread
    def construct_image(colour: Colour):
        buffer = BytesIO()

        with Color(str(colour)) as color, Image(width=100, height=100, background=color) as image:
            return image.make_blob(format='png')

    @command(aliases=['color'])
    async def colour(self, ctx: Context, *, colour: Colour):
        async with ctx.channel.typing:
            buffer = await self.construct_image(colour)

        await ctx.channel.messages.upload(fp=buffer, filename='solid_colour.png')

    @colour.subcommand()
    async def show(self, ctx: Context, *, colour: Colour):
        await self.colour(ctx, colour=colour)
