'''
Created on Apr 1, 2014

@author: nathan

This class handles dispatching UPD things. Basically it bootstraps the standard
ChatManager.client_connected method with a custom reader/writer, set up such
that incoming UDP datagrams are simply appended to the reader stream, and
writes to the writer stream are concatenated into datagrams and sent as units.
'''

import asyncio


class UDPChatWriter:
    '''
    Class emulating a StreamWriter to convert data to Datagrams and send it to
    the correct remote.
    '''
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


class UDPProtocol(asyncio.DatagramProtocol):
    '''
    This class handles dispatching datagrams to the appropriate clients and
    converting the data into a stream for the Client object.
    '''
    @classmethod
    def factory(cls, manager):
        return lambda: cls(manager)

    def __init__(self, manager):
        self.udp_clients = {}
        self.manager = manager

    # From asyncio.DatagramProtocol
    def connection_made(self, transport):
        self.transport = transport

    # From asyncio.DatagramProtocol
    def datagram_received(self, data, addr):
        self.manager.debug_print("Received Datagram\n")
        try:
            reader = self.udp_clients[addr]
        except KeyError:
            reader = self.start_client(addr)

        reader.feed_data(data)

    def start_client(self, addr):
        '''
        Create a new client, add it to the table, and return the reader.
        Doesn't check that addr is already in the table
        '''
        self.manager.debug_print("Creating new datagram client\n")
        reader = asyncio.StreamReader()
        writer = UDPChatWriter(self.transport, addr)

        self.udp_clients[addr] = reader

        asyncio.Task(self.client_coro(addr, reader, writer))

        return reader

    @asyncio.coroutine
    def client_coro(self, addr, reader, writer):
        '''
        Wrapper for ChatManager.client_connected. Ensures that the client is
        removed from the UDP table when it exits.
        '''
        try:
            yield from self.manager.client_connected(reader, writer)
        finally:
            self.manager.debug_print("Removing datagram client")
            del self.udp_clients[addr]
