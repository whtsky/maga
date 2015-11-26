import signal

import bencoder
import asyncio
import logging

from utils import generate_byte_string, generate_node_id, split_nodes, proper_infohash


TOKEN_LENGTH = 2

BOOTSTRAP_NODES = (
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881)
)


class Maga(asyncio.DatagramProtocol):
    def __init__(self, handler, loop=None, bootstrap_nodes=BOOTSTRAP_NODES):
        self.node_id = generate_node_id()
        self.transport = None
        self.loop = loop or asyncio.get_event_loop()
        self.bootstrap_nodes = bootstrap_nodes
        self.handler = handler
        self.__running = False

    def run(self, port=6881):
        coro = self.loop.create_datagram_endpoint(lambda: self, local_addr=('0.0.0.0', port))
        transport, _ = self.loop.run_until_complete(coro)

        self.bootstrap()
        async def beep():
            while self.__running:
                await asyncio.sleep(1)
                for node in self.bootstrap_nodes:
                    self.send_find_node_message(addr=node)

        def stop():
            self.__running = False
            self.loop.stop()

        asyncio.ensure_future(beep(), loop=self.loop)
        for signame in ('SIGINT', 'SIGTERM'):
            self.loop.add_signal_handler(getattr(signal, signame), stop)

        self.loop.run_forever()
        self.loop.close()

    def datagram_received(self, data, addr):
        try:
            msg = bencoder.bdecode(data)
        except:
            return

        try:
            self.handle_message(msg, addr)
        except:
            self.send_message(data={
                "t": msg["t"],
                "y": "e",
                "e": [202, "Server Error"]
            }, addr=addr)

    def handle_message(self, msg, addr):
        msg_type = msg.get(b"y", b"e")
        if msg_type == b"e":
            return

        if msg_type == b"r":
            return self.handle_response(msg, addr=addr)

        if msg_type == b'q':
            return asyncio.ensure_future(
                self.handle_query(msg, addr=addr), loop=self.loop
            )

    def handle_response(self, msg, addr):
        args = msg[b"r"]
        if b"nodes" in args:
            for node_id, ip, port in split_nodes(args[b"nodes"]):
                self.send_find_node_message(
                    addr=(ip, port),
                    node_id=node_id
                )

    async def handle_query(self, msg, addr):
        args = msg[b"a"]
        node_id = args[b"id"]
        query_type = msg[b"q"]
        if query_type == b"get_peers":
            infohash = proper_infohash(args[b"info_hash"])
            token = infohash[:TOKEN_LENGTH]
            self.send_message({
                "t": msg[b"t"],
                "y": "r",
                "r": {
                    "id": self.fake_node_id(node_id),
                    "nodes": "",
                    "token": token
                }
            }, addr=addr)
            await self.handler(infohash)
        elif query_type == b"announce_peer":
            tid = msg[b"t"]
            self.send_message({
                "t": tid,
                "y": "r",
                "r": {
                    "id": self.fake_node_id(node_id)
                }
            }, addr=addr)
            infohash = proper_infohash(args[b"info_hash"])
            await self.handler(infohash)
        elif query_type == b"find_node":
            tid = msg[b"t"]
            self.send_message({
                "t": tid,
                "y": "r",
                "r": {
                    "id": self.fake_node_id(node_id),
                    "nodes": ""
                }
            }, addr=addr)
        elif query_type == b"ping":
            self.pong_node(addr=addr, node_id=node_id)

    def ping_node(self, addr, node_id=None):
        self.send_message({
            "y": "q",
            "t": "pg",
            "q": "ping",
            "a": {
                "id": self.fake_node_id(node_id)
            }
        }, addr=addr)

    def bootstrap(self):
        for node in self.bootstrap_nodes:
            self.send_find_node_message(addr=node, target=self.node_id)

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.close()
        self.__running = False

    def send_message(self, data, addr):
        if "t" not in data:
            data["t"] = generate_byte_string(2)
        self.transport.sendto(bencoder.bencode(data), addr)

    def pong_node(self, addr, node_id):
        self.send_message({
            "t": generate_byte_string(2),
            "y": "r",
            "r": {
                "id": self.fake_node_id(node_id)
            }
        }, addr=addr)

    def fake_node_id(self, node_id=None):
        if node_id:
            return node_id[:-3]+self.node_id[-3:]
        return self.node_id

    def send_find_node_message(self, addr, node_id=None, target=None, t=b"fn"):
        if not target:
            target = generate_node_id()
        self.send_message({
            "t": t,
            "y": "q",
            "q": "find_node",
            "a": {
                "id": self.fake_node_id(node_id),
                "target": target
            }
        }, addr=addr)


if __name__ == "__main__":
    async def infohash_handler(infohash):
        logging.info(infohash)
    Maga(infohash_handler).run(6881)
