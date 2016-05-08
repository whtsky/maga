from maga import Maga

import logging
logging.basicConfig(level=logging.INFO)


class Crawler(Maga):
    async def handler(self, infohash, addr):
        logging.info(infohash)

crawler = Crawler()
crawler.run(6881)
