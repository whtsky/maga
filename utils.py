import os
import base64
import binascii
import cchardet as chardet
from struct import unpack
from socket import inet_ntoa


def proper_infohash(infohash):
    if isinstance(infohash, bytes):
        infohash = bytes_to_hex(infohash)
    return infohash.upper()


def guess_and_decode(bytes):
    result = chardet.detect(bytes)
    if result.get("confidence", 0) > 0.8:
        return bytes.decode(result["encoding"])
    return bytes.decode("GB18030")


def bytes_to_hex(bytes):
    return binascii.hexlify(bytes).decode('utf-8')


def vuze_encode(infohash):
    return base64.b32encode(binascii.unhexlify(infohash.encode())).decode()


def generate_byte_string(bit_size):
    return os.urandom(bit_size)


def generate_node_id(size=20):
    return generate_byte_string(size)


def split_nodes(nodes):
    length = len(nodes)
    if (length % 26) != 0:
        return

    for i in range(0, length, 26):
        nid = nodes[i:i+20]
        ip = inet_ntoa(nodes[i+20:i+24])
        port = unpack("!H", nodes[i+24:i+26])[0]
        yield nid, ip, port
