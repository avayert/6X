from io import BytesIO

from PIL import Image


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
