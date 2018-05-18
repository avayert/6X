from PIL.ImageFont import truetype
from io import BytesIO

from PIL import Image
from PIL.ImageDraw import Draw
from curious import event, EventContext, Role
from curious.commands import Plugin
from ruamel.yaml import YAML

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

    @event('role_update')
    async def colour_changed(self, ctx: EventContext, old: Role, new: Role):
        # We only care about colour changes
        if old.colour == new.colour:
            return

        channel = ctx.bot.find_channel(348933705923952641)

        # Weird
        if channel is None:
            print('channel not found')
            return

        with Image.new('RGB', (200, 100)) as img:
            draw = Draw(img)  # lol no context manager
            old_colour = Colour(old.colour)
            new_colour = Colour(new.colour)
            draw.rectangle([0, 0, 100, 100], fill=old_colour.rgb)
            draw.rectangle([100, 0, 200, 100], fill=new_colour.rgb)

            # 🙃 thanks pillow for SUCKING
            font = truetype('VCR_OSD_MONO.ttf', size=20)
            x, y = font.getsize('#000000')
            x, y = (100 - x) // 2, (100 - y) // 2

            draw.text((x, y), str(old_colour), align='center', font=font)
            draw.text((x + 100, y), str(new_colour), align='center', font=font)

            buffer = BytesIO()
            img.save(buffer, 'png')
            buffer.seek(0)

            await channel.messages.upload(buffer, filename='cool.png')
