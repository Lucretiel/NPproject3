'''
Created on Mar 17, 2014

@author: nathan

This class manages creating the client instances and forwarding messages
'''

import asyncio
import contextlib
import re
from sys import stderr

from npchat import common
from npchat.server.exceptions import ChatError, LineError
from npchat.server.client import Client


me_is_pattern = re.compile("ME IS (?P<username>\w+)\s*\Z")


class ChatManager:
    def __init__(self, randoms, random_rate, verbose, debug):
        '''
        Initialize a chat manager

          `randoms`: the list of random phrases to inject
          `verbose`: True for verbose output
          `debug`: True for debug output
          `random_rate`: How many normal messages to send between randoms
        '''
        self.chatters = {}
        self.random_rate = random_rate
        if random_rate:
            self.randoms = [b''.join(common.make_body(r))
                for r in randoms]

        if debug:
            self.debug_print = stderr.write
        else:
            self.debug_print = lambda message: None

    @asyncio.coroutine
    def serve_forever(self, ports):
        servers = []
        for port in ports:
            # Need 1 server for each port
            server = yield from asyncio.start_server(
                self.client_connected, None, port)
            # TODO: UDP

            # Get the listener task
            servers.append(server.wait_closed())

            self.debug_print("Listening on port {n}\n".format(n=port))

        yield from asyncio.wait(servers)

    @asyncio.coroutine
    def client_connected(self, reader, writer):
        '''
        Primary client handler coroutine. One is spawned per client connection.
        '''
        self.debug_print("Client Connected\n")

        # Ensure transport is closed at end, and handle errors
        with contextlib.closing(writer), self.handle_errors(writer):
            # Get the ME IS line
            line = yield from reader.readline()

            # Get the username
            match = me_is_pattern.match(line.decode('ascii'))
            if match is None:
                raise LineError("Malformed ME IS Line", line)
            name = match.group('username').casefold()

            # Add self to the client list, and remove when done
            with self.login(name, reader, writer) as client:
                yield from client.handle_messages(self)

    @contextlib.contextmanager
    def login(self, name, reader, writer):
        '''
        Attempt to login a username. Insert the client into the chatters
        dictionary, and remove it when the context leaves. Raise a ChatError if
        name is already in the chatters dictionary
        '''
        # If name already exists, send error and throw
        if name in self.chatters:
            raise ChatError("Username {name} already exists".format(name=name))

        client = Client(name, reader, writer, self.debug_print)

        # Add sender to chatters
        self.chatters[name] = client.message_sender(
            self.randoms, self.random_rate)

        # Write acknowledgment
        writer.write('OK\n'.encode('ascii'))

        # Get client info
        self.debug_print("Logged in user {name}\n".format(name=name))

        # Enter context, and remove from dictionary when leaving.
        try:
            yield client
        finally:
            del self.chatters[name]
            self.debug_print("Logged out user {name}\n".format(name=name))

    def send_to_recipients(self, sender, recipients, body_parts):
        '''
        Send a message to a list of recipients. Creates a FROM header, handles
        encoding, etc. Ignores recipients not in the list. If recipients is
        None, perform a broadcast
        '''
        message = (sender,
            b''.join(common.prepare_full_body(sender, body_parts)))

        if recipients is not None:
            for recipient in recipients:
                with contextlib.suppress(KeyError):
                    self.chatters[recipient.casefold()].send(message)
        else:
            for sender in self.chatters.values():
                sender.send(message)

    def broadcast(self, sender, body_parts):
        self.send_to_recipients(sender, None, body_parts)

    def who_is_here(self, recipient):
        self.send_to_recipients("SERVER", [recipient],
            common.make_body('\n'.join(self.chatters)))

    @contextlib.contextmanager
    def handle_errors(self, writer):
        '''
        Handler errors that leave the context. For ChatErrors, write a message
        to the client and log; for other Exceptions, send an error to the
        client and re-raise.
        '''
        try:
            yield

        # Handle chat errors
        except ChatError as e:
            message = "ERROR {e.message}\n".format(e=e)
            # Debug Print
            self.debug_print(message)

            # Inform client
            writer.write(message.encode('ascii'))

        # Inform client of other errors and reraise
        except Exception as e:
            writer.write('ERROR UNKNOWN SERVER ERROR\n'.encode('ascii'))
            raise
