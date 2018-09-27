from collections import namedtuple

from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from curio import spawn_thread
from curious import EventContext, Role, event
from curious.commands import Context, Plugin, command
from heapq import nsmallest
from ruamel.yaml import YAML
from typing import Dict, List

from sixx.plugins.utils import Colour
from sixx.plugins.utils.converters import RGBPart
from sixx.plugins.utils.pillow import add_title, antialiased_text, save_image

result = namedtuple('result', 'colour name')

# side width of the square shown in the role colour thing
SIDE_WIDTH = 200

# Fonts used for the before/after role colour thing.
# NOTE: You will need a font file with this name in your system fonts.
# Either change the name of some other font or just change the
# string below if it's broken (good design I know)
FONT_BIG = truetype('VCR_OSD_MONO.ttf', size=int(SIDE_WIDTH * (5 / 2) * 0.75 / 10))
FONT_SMALL = truetype('VCR_OSD_MONO.ttf', size=int(SIDE_WIDTH * (5 / 4) * 0.75 / 10))


def load_colours() -> Dict[Colour, str]:
    """
    Loads the name-value combinations from a YAML file.

    These combinations have been scraped from Wikipedia:
    - https://en.wikipedia.org/wiki/List_of_colors:_A%E2%80%93F
    - https://en.wikipedia.org/wiki/List_of_colors:_G%E2%80%93M
    - https://en.wikipedia.org/wiki/List_of_colors:_N%E2%80%93Z
    """
    yaml = YAML()

    with open('sixx/data/colours.yml', 'r') as f:
        data = yaml.load(f)
        data = {Colour(colour): name for colour, name in data.items()}
        return data


class Colours(Plugin):
    """
    Colour related commands.
    """
    colours = load_colours()

    def get_colour_names(self, colour: Colour, *, n=5):
        return [result(colour, name) for colour, name in
                nsmallest(n, self.colours.items(), key=lambda item: item[0].distance(colour))]

    @command()
    async def nearest(self, ctx: Context, colour: Colour, n: int = 1):
        # TODO text clipping, maybe allow hex as an optional arg?
        nearest = self.get_colour_names(colour, n=n)

        async with ctx.channel.typing:
            async with spawn_thread():
                with Image.new('RGBA', (SIDE_WIDTH, int(SIDE_WIDTH / 5 * len(nearest)))) as img:
                    draw = Draw(img)

                    for rectangle_index, (colour, name) in enumerate(nearest):
                        offset = int(rectangle_index * SIDE_WIDTH / 5)

                        draw.rectangle([0, 0 + offset, SIDE_WIDTH, SIDE_WIDTH / 5 + offset], fill=colour.rgb)

                        font_colour = (0, 0, 0) if colour.contrast(Colour(0x000000)) >= 15 else (255, 255, 255)
                        name = antialiased_text(name, FONT_SMALL, SIDE_WIDTH, int(SIDE_WIDTH / 5), fill=font_colour)
                        img.paste(name, (0, 0 + offset), name)

                    buffer = save_image(img)
        await ctx.channel.messages.upload(buffer, filename='cool.png')

    @command()
    async def rgb(self, ctx: Context, colour: Colour):
        """
        Converts a hex colour to RGB.
        """
        message = '```prolog\n'
        for letter, value in zip('RGB', colour.rgb):
            message += f'{letter}: {value:02} (0x{value:02X})\n'
        message += ' '.join(str(part) for part in colour.rgb)
        message += '\n```'

        await ctx.channel.messages.send(message)

    @command(name='hex')
    async def hex_(self, ctx: Context, *parts: RGBPart):
        await ctx.channel.messages.send('#' + ''.join(f'{part:02X}' for part in parts))

    @event('role_update')
    async def colour_changed(self, ctx: EventContext, old: Role, new: Role):
        # We only care about colour changes
        if old.colour == new.colour:
            return

        # TODO make this event configured per-server
        # TODO make channel configurable per server
        channel = new.guild.system_channel

        # Weird
        if channel is None:
            return

        async with spawn_thread():
            # one colour is 100x100 -> 200x100 is the image size
            with Image.new('RGBA', (2 * SIDE_WIDTH, SIDE_WIDTH)) as img:
                draw = Draw(img)  # Draws the coloured rectangles

                for rectangle_index, colour in enumerate(map(Colour, (old.colour, new.colour))):
                    offset = rectangle_index * SIDE_WIDTH
                    draw.rectangle([0 + offset, 0, SIDE_WIDTH + offset, SIDE_WIDTH], fill=colour.rgb)

                    # This makes text black if the contrast between black text and the background colour
                    # is high because white text becomes unreadable on light coloured backgrounds.
                    font_colour = (0, 0, 0) if colour.contrast(Colour(0x000000)) >= 15 else (255, 255, 255)
                    nearest_colour = self.get_colour_names(colour, n=1).pop().name

                    name = antialiased_text(nearest_colour, FONT_SMALL, SIDE_WIDTH, fill=font_colour, offset_y=3 / 4,
                                            wrap_width=18)
                    code = antialiased_text(str(colour).upper(), FONT_BIG, SIDE_WIDTH, fill=font_colour)

                    img.paste(name, (0 + offset, 0), name)
                    img.paste(code, (0 + offset, 0), code)

                img = add_title(img, new.name, FONT_SMALL, height=25)

                buffer = save_image(img)
        await channel.messages.upload(buffer, filename='cool.png')
