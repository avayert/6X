import re
from curious.commands import Context
from curious.commands.exc import ConversionFailedError
from typing import Tuple

colour_pattern = re.compile(r'(#|0x)?([A-Za-z0-9]{1,6})')
RGB = Tuple[int, int, int]


class Colour:
    """
    A class that represents a colour.
    """

    def __init__(self, value: int):
        self.value = value

    def get_part(self, part) -> int:
        string = f'{self.value:06x}'
        piece = slice(part * 2, part * 2 + 2)
        return int(string[piece], base=16)

    @property
    def red(self) -> int:
        return self.get_part(0)

    r = red

    @property
    def green(self) -> int:
        return self.get_part(1)

    g = green

    @property
    def blue(self) -> int:
        return self.get_part(2)

    b = blue

    @property
    def rgb(self) -> RGB:
        return self.r, self.g, self.b

    def __repr__(self):
        return '{0.__class__.__name__}({0.value})'.format(self)

    def __str__(self):
        return f'#{self.value:06x}'


def convert_hex_colour(annotation, ctx: Context, arg: str) -> Colour:
    """
    Converts a string representation of a hex colour into an instance of Colour.
    """
    arg = colour_pattern.sub(r'\2', arg)

    try:
        value = int(arg, base=16)
    except ValueError:
        raise ConversionFailedError(ctx, arg, Colour, 'Invalid value.')
    else:
        return Colour(value)


Context.add_converter(Colour, convert_hex_colour)
