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
        async def handler(self, infohash, addr):
            logging.info(addr)
            logging.info(infohash)


    # Or, if you want to have more control

    class Crawler(Maga):
        async def handle_get_peers(self, infohash, addr):
            logging.info(addr)
            logging.info(infohash)

        async def handle_announce_peer(self, infohash, addr):
            logging.info(addr)
            logging.info(infohash)


    crawler = Crawler()
    crawler.run(6881)


ChangeLog
----------

Version 2.0.0
~~~~~~~~~~~~~~~

+ Add `handle_get_peers`, `handle_announce_peer` function.
+ Add `addr` param in `handler`