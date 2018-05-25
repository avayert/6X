"""
I hate pillow.
"""
import numpy as np
import random
import textwrap
from PIL import Image, ImageFont
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
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


def add_title(image: Image, text: str, font: ImageFont, height: int, **text_kwargs):
    """
    Adds a title strip to the top of the image.

    Changes the size of the image to be `image.size + (0, height)`

    See this for reference: https://cdn.discordapp.com/attachments/400042308189290509/448185670339395605/cool.png
    :param image: The image to add the title to
    :param text: The text to be written on the title
    :param font: The font that will be used to write the title text
    :param height: The height of the title
    :param text_kwargs: Extra keyword arguments to be passed into antialiased_text
    :return: New image with the title
    """
    f_width, f_height = font.getsize(text)

    if f_height > height:
        raise ValueError('Height of title must be larger than the font')

    x, y = image.size
    with Image.new('RGBA', (x, y + height)) as img:
        draw = Draw(img)

        img.paste(image, (0, height), image)

        with Image.new('RGBA', (x, y + height)) as shadow:
            # Draw the shadow box and apply blur
            cool = Draw(shadow)
            for i in range(1, 6):
                cool.rectangle([(0, height + i), (x, height + 1 + i)], fill=(38, 38, 38, 31 * (6 - i)))

            img.paste(shadow, (0, 0), shadow)

        draw.rectangle([0, 0, x, height], fill=(32, 34, 37))

        text = antialiased_text(text, font, size_x=x, size_y=height, fill=(255, 255, 255), **text_kwargs)
        img.paste(text, (0, 0), text)

        return img.copy()


def antialiased_text(text: str, font: ImageFont, size_x: int, size_y: int = None, *, offset_x: float = 1 / 2,
                     offset_y: float = 1 / 2, wrap_width: int = 50, msaa_size: int = 2, **draw_kwargs) -> Image:
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
    :param wrap_width: The length at which strings should be wrapped
    :return: An image with the desired text
    """
    if size_y is None:
        size_y = size_x

    font = truetype(font.path, size=font.size * msaa_size)

    with Image.new('RGBA', (size_x * msaa_size, size_y * msaa_size)) as image:
        draw = Draw(image)

        for index, string in enumerate(textwrap.wrap(text, wrap_width), start=-1):
            width, height = font.getsize(string)
            pos = (size_x * msaa_size - width) / offset_x ** -1, (size_y * msaa_size - height * -index) / offset_y ** -1
            draw.text(pos, string, font=font, **draw_kwargs)

        return image.resize((size_x, size_y), resample=Image.ANTIALIAS)


def add_scanlines(image: Image, *, transparency: int = 50):
    """
    Adds a scanline effect to an image.
    :param image: The image to add the effect to.
    :return: An image with the desired effect
    """

    # Makes alternating rows of  transparent black and white strips
    arr = np.empty((image.height, image.width, 4), dtype=np.uint8)
    arr[0::2] = (255, 255, 255, transparency)
    arr[1::2] = (0, 0, 0, transparency)

    with Image.fromarray(arr, 'RGBA') as img:
        image.paste(img, mask=img)

    return image


def add_noise(image: Image, *, transparency: int = 50):
    """
    Adds a scanline effect to an image.
    :param image: The image to add the effect to.
    :return: An image with the desired effect
    """

    arr = np.empty((image.height, image.width, 4))

    pixels = (0, 0, 0, transparency), (255, 255, 255, transparency)
    for y in range(image.height):
        for x in range(image.width):
            arr[y][x] = random.choice(pixels)

    with Image.fromarray(arr, 'RGBA') as img:
        image.paste(img, mask=img)

    return image
