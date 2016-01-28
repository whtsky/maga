Maga
====


A DHT crawler framework using asyncio.


Usage
-----
.. code-block:: python

    from maga import Maga
    
    import logging
    logging.basicConfig(level=logging.INFO)
    
    
    class Crawler(Maga):
        async def handler(self, infohash):
            logging.info(infohash)
    
    crawler = Crawler()
    crawler.run(6881)

