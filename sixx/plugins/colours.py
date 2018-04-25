from curio import async_thread
from curious.commands import Context, Plugin, command
from ruamel.yaml import YAML
from typing import List
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

from sixx.plugins.utils import Colour


def load_colours():
    yaml = YAML()

    with open('sixx/data/colours.yml', 'r') as f:
        return yaml.load(f)


class Colours(Plugin):
    """
    Colour related commands.
    """
    colours = load_colours()

    @staticmethod
    @async_thread
    def static_colours(colours: List[Colour]):
        with Drawing() as draw, Image(width=100 * len(colours), height=100) as image:
            for start, colour in enumerate(colours):
                draw.fill_color = Color(str(colour))
                draw.rectangle(left=100 * start, right=100 * (start + 1), top=0, bottom=100)
                draw(image)

            return image.make_blob(format='png')

    @command(aliases=['color'])
    async def colour(self, ctx: Context, *, colours: List[Colour]):
        async with ctx.channel.typing:
            buffer = await self.static_colours(colours)

        await ctx.channel.messages.upload(fp=buffer, filename='solid_colour.png')

    @colour.subcommand()
    async def show(self, ctx: Context, *, colours: List[Colour]):
        await self.colour(ctx, colours=colours)

    @colour.subcommand()
    async def name(self, ctx, *, colour: Colour):
        value, name = self.find_nearest_colour(colour.value)
        image = await self.static_colours([colour])

        await ctx.channel.messages.upload(fp=image, filename='colour.png', message_content=name)

    def find_nearest_colour(self, value):
        if value in self.colours:
            return value, self.colours[value]

        key = min(self.colours.keys(), key=lambda item: abs(item - value))
        return value, self.colours[key]
