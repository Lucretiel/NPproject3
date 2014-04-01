'''
Created on Apr 1, 2014

@author: nathan

This class handles dispatching UPD things. It is closely tied to the Manager
class, but is kept separate to keep Manager's implementation simple.
'''

from asyncio import DatagramProtocol, StreamReader
from npchat import common
import asyncio


class UDPChatWriter:
    def __init__(self, transport, addr):
        self.transport = transport
        self.addr = addr

    def write(self, data):
        self.transport.sendto(data, self.addr)

    def writelines(self, data):
        self.write(b''.join(data))

    def close(self):
        self.transport.close()

    def get_extra_info(self, info):
        return {'peername': self.addr}[info]


class UDPProtocol(DatagramProtocol):
    @classmethod
    def factory(cls, manager):
        return lambda: cls(manager)

    def __init__(self, manager):
        self.udp_clients = {}
        self.manager = manager

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.manager.debug_print("Received Datagram\n")
        try:
            reader = self.udp_clients[addr]
        except KeyError:
            reader = self.start_client(addr)

        reader.feed_data(data)

    def error_received(self, exc):
        print("ERROR:", exc)

    def start_client(self, addr):
        self.manager.debug_print("Creating new datagram client\n")
        reader = StreamReader()
        writer = UDPChatWriter(self.transport, addr)

        self.udp_clients[addr] = reader

        asyncio.Task(self.client_coro(addr, reader, writer))

        return reader

    @asyncio.coroutine
    def client_coro(self, addr, reader, writer):
        try:
            yield from self.manager.client_connected(reader, writer)
        finally:
            self.manager.debug_print("Removing datagram client")
            del self.udp_clients[addr]

