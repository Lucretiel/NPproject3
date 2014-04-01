'''
Created on Apr 1, 2014

@author: nathan

This class handles dispatching UPD things. It is closely tied to the Manager
class, but is kept separate to keep Manager's implementation simple.
'''

from asyncio import DatagramProtocol
from npchat import common
import asyncio


class UDPChatWriter:
    def __init__(self, transport, addr):
        self.transport = transport
        self.addr = addr

    def write(self, data):
        self.transport.write(data, self.addr)

    def writelines(self, data):
        self.write(b''.join(data))

    def close(self):
        self.transport.close()


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
        try:
            client = self.udp_clients[addr]
        except KeyError:
            client = self.udp_clients[addr] = self.client_handler(addr)

        client.send(data)

    @common.consumer
    def client_handler(self, addr):
        reader = asyncio.StreamReader()
        writer = UDPChatWriter(self.transport, addr)



