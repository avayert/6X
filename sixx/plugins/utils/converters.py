from math import sqrt

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

    def _get_part(self, part) -> int:
        string = f'{self.value:06x}'
        piece = slice(part * 2, part * 2 + 2)
        return int(string[piece], base=16)

    @property
    def red(self) -> int:
        return self._get_part(0)

    r = red

    @property
    def green(self) -> int:
        return self._get_part(1)

    g = green

    @property
    def blue(self) -> int:
        return self._get_part(2)

    b = blue

    @property
    def rgb(self) -> RGB:
        return self.r, self.g, self.b

    def distance(self, other: 'Colour'):
        # Taken from some wikipedia article I'm too lazy to dig it up
        r1, g1, b1 = self.rgb
        r2, g2, b2 = other.rgb
        return sqrt((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2)

    def luminance(self) -> float:
        """
        Calculate the luminance of the colour.

        Based on information from https://www.w3.org/TR/WCAG20-TECHS/G18.html
        """
        def convert(value):
            value /= 255

            if value <= 0.03928:
                return value / 12.92
            else:
                return ((value + 0.055) / 1.055) ** 2.4

        r, g, b = map(convert, self.rgb)

        return r * 0.2126 + g * 0.7152 + b * 0.0722

    def contrast(self, other: 'Colour'):
        """
        Calculate the contrast between two colours.

        Based on information from https://www.w3.org/TR/WCAG20-TECHS/G18.html
        """
        return (self.luminance() + 0.05) / (other.luminance() + 0.05)

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
