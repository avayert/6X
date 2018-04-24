import logging

import curio

from sixx.bot import main

if __name__ == '__main__':
    handler = logging.FileHandler(filename='sixx.log', encoding='utf-8', mode='w')
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
        handlers=[handler]
    )
    curio.run(main)
