from collections import namedtuple

from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from curious import EventContext, Role, event
from curious.commands import Context, Plugin, command
from heapq import nsmallest
from io import BytesIO
from ruamel.yaml import YAML
from typing import Dict

from sixx.plugins.utils import Colour

result = namedtuple('result', 'colour name')

# side width of the square shown in the role colour thing
SIDE_WIDTH = 200

# Fonts used for the before/after role colour thing.
# NOTE: You will need a font file with this name in your system fonts.
# Either change the name of some other font or just change the
# string below if it's broken (good design I know)
FONT_BIG = truetype('VCR_OSD_MONO.ttf', size=int(SIDE_WIDTH * (5 / 2) * 0.75))
FONT_SMALL = truetype('VCR_OSD_MONO.ttf', size=int(SIDE_WIDTH * (5 / 4) * 0.75))


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

        with Image.new('RGBA', (SIDE_WIDTH, int(SIDE_WIDTH / 5 * len(nearest)))) as img:
            draw = Draw(img)

            for rectangle_index, (colour, name) in enumerate(nearest):
                offset = int(rectangle_index * SIDE_WIDTH / 5)

                draw.rectangle([0, 0 + offset, SIDE_WIDTH, SIDE_WIDTH / 5 + offset], fill=colour.rgb)

                with Image.new('RGBA', (SIDE_WIDTH * 10, int((SIDE_WIDTH / 5) * 10))) as aa_img:
                    aa_draw = Draw(aa_img)

                    x, y = FONT_SMALL.getsize(name)
                    x, y = (SIDE_WIDTH * 10 - x) / 2, ((SIDE_WIDTH / 5) * 10 - y) / 2

                    font_colour = (0, 0, 0) if colour.contrast(Colour(0x000000)) >= 15 else (255, 255, 255)

                    aa_draw.text((x, y), name, font=FONT_SMALL, fill=font_colour)

                    aa_img = aa_img.resize((SIDE_WIDTH, int(SIDE_WIDTH / 5)), resample=Image.ANTIALIAS)
                    img.paste(aa_img, (0, 0 + offset), aa_img)

            buffer = BytesIO()
            img.save(buffer, 'png')
            buffer.seek(0)  # needs to be here or it'll send a 0-byte file

            await ctx.channel.messages.upload(buffer, filename='cool.png')

    @event('role_update')
    async def colour_changed(self, ctx: EventContext, old: Role, new: Role):
        # We only care about colour changes
        if old.colour == new.colour:
            return

        # TODO make this event configured per-server
        # TODO make channel configurable per server
        channel = ctx.bot.find_channel(348933705923952641)

        # Weird
        if channel is None:
            return

        # one colour is 100x100 -> 200x100 is the image size
        with Image.new('RGBA', (2 * SIDE_WIDTH, SIDE_WIDTH)) as img:
            draw = Draw(img)  # Draws the coloured rectangles

            for rectangle_index, colour in enumerate(map(Colour, (old.colour, new.colour))):
                offset = rectangle_index * SIDE_WIDTH
                draw.rectangle([0 + offset, 0, SIDE_WIDTH + offset, SIDE_WIDTH], fill=colour.rgb)

                # Pillow doesn't antialias text and has no support for it so we create a larger
                # image than the original with only the text, then resize it with the antialias
                # filter and paste it on top of the actual image we want to send to discord.
                with Image.new('RGBA', (SIDE_WIDTH * 10, SIDE_WIDTH * 10)) as aa_img:
                    aa_draw = Draw(aa_img)

                    x, y = FONT_BIG.getsize('#000000')
                    x, y = (SIDE_WIDTH * 10 - x) / 2, (SIDE_WIDTH * 10 - y) / 2  # top left corner of the text

                    # This makes text black if the contrast between black text and the background colour
                    # is high because white text becomes unreadable on light coloured backgrounds.
                    font_colour = (0, 0, 0) if colour.contrast(Colour(0x000000)) >= 15 else (255, 255, 255)

                    aa_draw.text((x, y), str(colour).upper(), font=FONT_BIG, fill=font_colour)

                    nearest_colour = self.get_colour_names(colour, n=1).pop().name
                    x, y = FONT_SMALL.getsize(nearest_colour)
                    x, y = (SIDE_WIDTH * 10 - x) // 2, (SIDE_WIDTH * 10 - y) // 4 * 3

                    aa_draw.text((x, y), nearest_colour, font=FONT_SMALL, fill=font_colour)

                    aa_img = aa_img.resize((SIDE_WIDTH, SIDE_WIDTH), resample=Image.ANTIALIAS)
                    img.paste(aa_img, (0 + offset, 0), aa_img)

            # save image so we can send it
            buffer = BytesIO()
            img.save(buffer, 'png')
            buffer.seek(0)  # needs to be here or it'll send a 0-byte file

            await channel.messages.upload(buffer, filename='cool.png')
