"""
I hate pillow.
"""

from PIL import Image, ImageFont
from PIL.ImageDraw import Draw
from io import BytesIO


def save_image(image: Image, *, format='png') -> BytesIO:
    """
    Saves a pillow image to a bytes buffer.

    :param image: The image to be saved.
    :param format: The format in which the image will be saved.
    :return:
    """
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def antialiased_text(text: str, font: ImageFont, size_x: int, size_y: int = None, *, offset_x: float = 1 / 2,
                     offset_y: float = 1 / 2, **draw_kwargs) -> Image:
    """
    Returns a new image with antialiased text that you can then paste on your source image.

    Pillow has no support for antialiasing text so the way we achieve the same thing is
    creating an image multiple times larger and then resizing it with the antialias filter.

    :param text: The text to be written
    :param font: The font to be used
    :param size_x: The width of the desired image
    :param size_y: The height of the desired image
    :param offset_x: How far away from the top the text will be
    :param offset_y: How far away from the left the text will be
    :param draw_kwargs: Additional keyword arguments to the `draw` method
    :return: An image with the desired text
    """
    if size_y is None:
        size_y = size_x

    with Image.new('RGBA', (size_x * 10, size_y * 10)) as image:
        draw = Draw(image)

        width, height = font.getsize(text)
        pos = (size_x * 10 - width) / offset_x ** -1, (size_y * 10 - height) / offset_y ** -1

        draw.text(pos, text, font=font, **draw_kwargs)

        a = image.resize((size_x, size_y), resample=Image.ANTIALIAS)
        return a
