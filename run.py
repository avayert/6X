import sys

import curio
import logging

from sixx.bot import main

if __name__ == '__main__':
    handlers = [logging.FileHandler(filename='sixx.log', encoding='utf-8', mode='w')]

    level = logging.WARNING

    if any(arg == '--debug' for arg in sys.argv):
        handlers.append(logging.StreamHandler(sys.stdout))
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    curio.run(main)
