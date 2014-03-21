'''
Created on Mar 17, 2014

@author: nathan

This class manages creating the client instances and forwarding messages
'''

import asyncio
import re
import contextlib
import random
from collections import namedtuple
from sys import stderr

from npchat import util, verbose


def selector(**patterns):
    return '|'.join('(?P<{name}>{pattern})'.format(name=name, pattern=pattern)
        for name, pattern in patterns.items())

me_is_pattern = re.compile("ME IS (?P<username>\w+)\s*\Z", re.I)

action_pattern = re.compile(
    selector(
        send="SEND(?P<users>( \w+)+)\s*\Z",
        broadcast="BROADCAST\s*\Z",
        logout="LOGOUT\s*\Z",
        whoishere="WHO IS HERE\s*\Z",
        whoami="WHO AM I\s*\Z"),
    re.I)


short_pattern = re.compile('(?P<body_size>[0-9]{1,2})\s*\Z', re.I)
chunk_pattern = re.compile('C(?P<chunk_size>[0-9]{1,3})\s*\Z', re.I)

body_pattern = re.compile(
    selector(
        chunk=chunk_pattern.pattern,
        short=short_pattern.pattern),
    re.I)


# Simple type to hold all the connected client data
Client = namedtuple('Client', ('name', 'reader'))


class ChatError(RuntimeError):
    @property
    def message(self):
        return self.args[0]


class NameExistsError(ChatError):
    '''
    Subclass of ChatError to enable that specific ERROR print in a non-extended
    protocol. It only has the name, and dynamically emits a message
    '''
    @property
    def message(self):
        return "Name {name} already exists".format(name=self.args[0])


class LineError(ChatError):
    '''
    Error with the line. Usually means a parse or unknown command error.
    '''
    @property
    def message(self):
        return "{error}: {line}".format(
            error=self.args[0], line=self.args[1].decode('ascii'))


# TODO: GET RID OF ALL THE FUCKING if self.verbose CALLS GODDAMNIT
class ChatManager:
    def __init__(self, randoms, random_rate, verbose, debug, extended):
        '''
        Initialize a chat manager

          `randoms`: the list of random phrases to inject
          `verbosity`: True for verbose output
          `debug`: True for debug output
          `random_rate`: How many normal messages to send between randoms
        '''
        self.chatters = {}
        self.random_rate = random_rate
        if random_rate:
            self.randoms = [b''.join(util.make_body(r + '\n'))
                for r in randoms]
        self.verbose = verbose
        self.debug = debug
        self.extended = extended

    def debug_print(self, message):
        if self.debug:
            stderr.write(message)

    @asyncio.coroutine
    def serve_forever(self, ports):
        servers = []
        for port in ports:
            # Need 1 server for each port
            server = yield from asyncio.start_server(
                self.client_connected, None, port)

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
        # Get wrappers
        if self.verbose:
            reader, writer = verbose.make_verbose_reader_writer(
                reader, writer)

        # Ensure transport is closed at end, and handle errors
        with contextlib.closing(writer), self.handle_errors(writer):
            # Get the ME IS line
            line = yield from reader.readline()
            if self.verbose:
                reader.print_cached()

            # Get the username
            match = me_is_pattern.match(line.decode('ascii'))
            if match is None:
                raise LineError("Malformed ME IS Line", line)
            name = match.group('username')

            # Add self to the client list, and remove when done
            with self.login(name, reader, writer) as client:
                yield from self.core_loop(client)

    @contextlib.contextmanager
    def login(self, name, reader, writer):
        '''
        Attempt to login a username. Insert the client into the chatters
        dictionary, and remove it when the context leaves. Raise a ChatError if
        name is already in the chatters dictionary
        '''
        # If name already exists, send error and throw
        if name in self.chatters:
            raise NameExistsError(name)

        # Create client sender
        @util.consumer
        def client_sender():
            '''
            Consumer-generator to handle sending messages to clients. Primarily
            responsible for also injecting random bonus messages
            '''
            # If we're using randoms
            if self.random_rate > 0 and self.randoms:
                while True:
                    # set would be better, but random.choice needs a sequence
                    recent = list()

                    # Perform random_rate normal writes, then a random write
                    for _ in range(self.random_rate):
                        sender, body = yield
                        recent.append(sender)
                        writer.write(body)
                        if self.verbose:
                            writer.print_cached()

                    writer.writelines((
                        util.make_sender_line(random.choice(recent)),
                        random.choice(self.randoms)))
                    if self.verbose:
                        writer.print_cached_random()
            else:
                while True:
                    sender, body = yield
                    writer.write(body)
                    if self.verbose:
                        writer.print_cached()

        # Add sender to chatters
        self.chatters[name] = client_sender()

        # Write acknowledgment
        writer.write('OK\n'.encode('ascii'))
        if self.verbose:
            writer.print_cached()

        # Get client info
        self.debug_print("Logged in user {name}\n".format(name=name))

        # NOW we can attach the name. Before it wasn't ok, because reasons.
        reader.name = name
        writer.name = name

        # Enter context, and remove from dictionary when leaving
        try:
            yield Client(name, reader)
        finally:
            del self.chatters[name]
            self.debug_print("Logged out user {name}\n".format(name=name))

    @asyncio.coroutine
    def core_loop(self, client):
        '''
        This coroutine handles serving messages, after all the initial
        handshaking and context stuff is set up.
        '''
        while True:
            # Get the send line (SEND name name / BROADCAST)
            line = yield from client.reader.readline()

            # If no data was received, assume connection was closed
            if not line:
                break

            # Match the action and execute
            match = action_pattern.match(line.decode('ascii'))
            if match is None:
                raise LineError("Malformed send line", line)

            elif match.lastgroup == 'send':
                yield from self.read_and_send(client,
                    (r for r in match.group('users').split()
                     if r in self.chatters))

            elif match.lastgroup == 'broadcast':
                yield from self.read_and_send(client,
                    (r for r in self.chatters if r != client.name))

            elif match.lastgroup == 'whoishere':
                if(self.verbose):
                    client.reader.print_cached()
                self.send_to_recipients("SERVER", [client.name],
                    util.make_body('\n'.join(self.chatters)))

            elif match.lastgroup == 'whoami':
                if(self.verbose):
                    client.reader.print_cached()
                self.send_to_recipients("SERVER", [client.name],
                    util.make_body(client.name))

            elif match.lastgroup == 'logout':
                if(self.verbose):
                    client.reader.print_cached()
                break

            else:
                raise LineError("Action not implemented", line)

    @asyncio.coroutine
    def read_and_send(self, client, recipients):
        '''
        Read a body and send to a list of recipients. This is a coroutine, so
        the list should be generated lazily, such that it isn't evaluated until
        the actual sends, at the end, in case users log out during a context
        switch
        '''
        # Get the first body header line
        line = yield from client.reader.readline()

        # Parse body header line
        match = body_pattern.match(line.decode('ascii'))
        if match is None:
            raise LineError("Malformed body header", line)

        body_parts = [line]

        # Read body
        if match.lastgroup == 'short':
            # Get body size
            size = int(match.group('body_size'))

            # Read body
            body = yield from client.reader.readexactly(size)
            body_parts.append(body)

        elif match.lastgroup == 'chunk':
            while True:
                # Get chunk size
                size = int(match.group('chunk_size'))

                # Break on chunk size of 0
                if size == 0:
                    break

                # Read chunk
                chunk = yield from client.reader.readexactly(size)
                body_parts.append(chunk)

                # Get next chunk line
                line = yield from client.reader.readline()
                match = chunk_pattern.match(line.decode('ascii'))
                if match is None:
                    raise LineError("Malformed chunk header", line)

                # Add chunk line to body
                body_parts.append(line)
        else:
            raise ChatError("Unknown Server Error")

        if(self.verbose):
            client.reader.print_cached()

        self.send_to_recipients(client.name, recipients, body_parts)

    def send_to_recipients(self, sender, recipients, body_parts):
        message = (
            sender,
            b''.join(util.prepare_full_body(sender, body_parts)))

        for recipient in recipients:
            self.chatters[recipient].send(message)

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
            message = "ERROR: {e.message}\n".format(e=e)
            # Debug Print
            self.debug_print(message)

            # Inform client
            if self.extended:
                writer.write(message.encode('ascii'))
                if self.verbose:
                    writer.print_cached()

            # If we're not using extended, send normal error message
            elif isinstance(e, NameExistsError):
                writer.write("ERROR\n".encode('ascii'))
                if self.verbose:
                    writer.print_cached()

        # Inform client of other errors and reraise
        except Exception as e:
            if self.extended:
                writer.write('UNKNOWN SERVER ERROR\n'.encode('ascii'))
            raise
