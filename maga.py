import asyncio
import binascii
import os
import signal

from socket import inet_ntoa
from struct import unpack

import bencoder


def proper_infohash(infohash):
    if isinstance(infohash, bytes):
        # Convert bytes to hex
        infohash = binascii.hexlify(infohash).decode('utf-8')
    return infohash.upper()


def random_node_id(size=20):
    return os.urandom(size)


def split_nodes(nodes):
    length = len(nodes)
    if (length % 26) != 0:
        return

    for i in range(0, length, 26):
        nid = nodes[i:i+20]
        ip = inet_ntoa(nodes[i+20:i+24])
        port = unpack("!H", nodes[i+24:i+26])[0]
        yield nid, ip, port


__version__ = '2.0.0'


BOOTSTRAP_NODES = (
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881)
)


class Maga(asyncio.DatagramProtocol):
    def __init__(self, loop=None, bootstrap_nodes=BOOTSTRAP_NODES, interval=1):
        self.node_id = random_node_id()
        self.transport = None
        self.loop = loop or asyncio.get_event_loop()
        self.bootstrap_nodes = bootstrap_nodes
        self.__running = False
        self.interval = interval

    def stop(self):
        self.__running = False
        self.loop.call_later(self.interval, self.loop.stop)

    async def auto_find_nodes(self):
        self.__running = True
        while self.__running:
            await asyncio.sleep(self.interval)
            for node in self.bootstrap_nodes:
                self.find_node(addr=node)

    def run(self, port=6881):
        coro = self.loop.create_datagram_endpoint(
                lambda: self, local_addr=('0.0.0.0', port)
        )
        transport, _ = self.loop.run_until_complete(coro)

        for signame in ('SIGINT', 'SIGTERM'):
            self.loop.add_signal_handler(getattr(signal, signame), self.stop)

        for node in self.bootstrap_nodes:
            # Bootstrap
            self.find_node(addr=node, node_id=self.node_id)

        asyncio.ensure_future(self.auto_find_nodes(), loop=self.loop)
        self.loop.run_forever()
        self.loop.close()

    def datagram_received(self, data, addr):
        try:
            msg = bencoder.bdecode(data)
        except:
            return
        try:
            self.handle_message(msg, addr)
        except Exception as e:
            self.send_message(data={
                "t": msg["t"],
                "y": "e",
                "e": [202, "Server Error"]
            }, addr=addr)
            raise e

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
                self.ping(addr=(ip, port))

    async def handle_query(self, msg, addr):
        args = msg[b"a"]
        node_id = args[b"id"]
        query_type = msg[b"q"]
        if query_type == b"get_peers":
            infohash = args[b"info_hash"]
            infohash = proper_infohash(infohash)
            token = infohash[:2]
            self.send_message({
                "t": msg[b"t"],
                "y": "r",
                "r": {
                    "id": self.fake_node_id(node_id),
                    "nodes": "",
                    "token": token
                }
            }, addr=addr)
            await self.handle_get_peers(infohash, addr)
        elif query_type == b"announce_peer":
            infohash = args[b"info_hash"]
            tid = msg[b"t"]
            self.send_message({
                "t": tid,
                "y": "r",
                "r": {
                    "id": self.fake_node_id(node_id)
                }
            }, addr=addr)
            await self.handle_announce_peer(proper_infohash(infohash), addr)
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
            self.send_message({
                "t": b"tt",
                "y": "r",
                "r": {
                    "id": self.fake_node_id(node_id)
                }
            }, addr=addr)
        self.find_node(addr=addr, node_id=node_id)

    def ping(self, addr, node_id=None):
        self.send_message({
            "y": "q",
            "t": "pg",
            "q": "ping",
            "a": {
                "id": self.fake_node_id(node_id)
            }
        }, addr=addr)

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.__running = False
        self.transport.close()

    def send_message(self, data, addr):
        data.setdefault("t", b"tt")
        self.transport.sendto(bencoder.bencode(data), addr)

    def fake_node_id(self, node_id=None):
        if node_id:
            return node_id[:-1]+self.node_id[-1:]
        return self.node_id

    def find_node(self, addr, node_id=None, target=None):
        if not target:
            target = random_node_id()
        self.send_message({
            "t": b"fn",
            "y": "q",
            "q": "find_node",
            "a": {
                "id": self.fake_node_id(node_id),
                "target": target
            }
        }, addr=addr)

    async def handle_get_peers(self, infohash, addr):
        await self.handler(infohash, addr)

    async def handle_announce_peer(self, infohash, addr):
        await self.handler(infohash, addr)

    async def handler(self, infohash, addr):
        raise NotImplementedError()
