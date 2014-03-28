'''
Created on Mar 24, 2014

@author: nathan
'''

import asyncio
import random
import re

from npchat import common
from npchat.server.exceptions import LineError, ServerError
import contextlib


body_pattern = re.compile(
    '(?:C(?P<chunk_size>[0-9]{1,3})|(?P<short_size>[0-9]{1,2}))\s*\Z')

chunk_pattern = re.compile(
    'C(?P<chunk_size>[0-9]{1,3})\s*\Z')


class Logout(Exception):
    ''' Raised to indicate logout '''
    pass


class ActionHandlers:
    '''
    ActionHandlers registers functions to handle different actions.
    '''
    def __init__(self):
        self.handlers = {}

    def handler(self, action_prefix):
        '''
        Register a function as a handler for an action
        '''
        def decorator(func):
            self.handlers[action_prefix] = func
            return func
        return decorator

    def get_handler(self, line):
        '''
        Lookup an action handler. Raise a KeyError if it doens't exist
        '''
        for action, handler in self.handlers.items():
            if line.startswith(action):
                return action, handler
        else:
            raise KeyError


class Client:
    #####################
    # ACTION HANDLING
    #####################

    # Dictionary of registered actions
    action_handlers = ActionHandlers()

    ##################################
    # PRIMARY CLIENT IMPLEMENTATION
    ##################################

    def __init__(self, name, reader, writer, debug_print, randoms,
            random_rate):
        self.name = name
        self.reader = reader
        self.writer = writer
        self.debug_printer = debug_print
        self.send_message = self.message_sender(randoms, random_rate).send

    def debug_print(self, what):
        self.debug_printer(what.format(name=self.name))

    @asyncio.coroutine
    def handle_messages(self, manager):
        '''
        Core message handling loop
        '''
        # Loop until a logout
        with contextlib.suppress(Logout, asyncio.IncompleteReadError):
            while True:
                self.debug_print("{name}: awaiting action\n")
                # Get the send line (SEND name name / BROADCAST)
                line = yield from self.reader.readline()

                yield from self.handle_action(line, manager)

    @asyncio.coroutine
    def handle_action(self, line, manager):
        '''
        Dispatch to an action handler.
        '''
        decoded = line.decode('ascii')
        try:
            # Get handler. May raise KeyError
            action, handler = self.action_handlers.get_handler(decoded)

            # Extract arguments. May raise ValueError
            from_user, *lineargs = decoded[len(action):].split()

            # Match username
            if from_user.casefold() != self.name:
                raise LineError("Name doesn't match", line)

        except KeyError as e:  # Handler lookup failed
            raise LineError("Invalid action", line) from e

        except ValueError as e:  # Extraction of from_user failed
            raise LineError("No from_user specified", line) from e

        else:
            return handler(self, lineargs, manager)

    @action_handlers.handler("SEND")
    @asyncio.coroutine
    def handle_send(self, recipients, manager):
        self.debug_print("{name}: Performing send\n")
        return self.read_and_send(manager, recipients)

    @action_handlers.handler("BROADCAST")
    @asyncio.coroutine
    def handle_broadcast(self, _, manager):
        self.debug_print("{name}: Performing broadcast\n")
        return self.read_and_send(manager)

    @action_handlers.handler("WHO HERE")
    @asyncio.coroutine
    def handle_who_here(self, _, manager):
        self.debug_print("{name}: Checking who is here\n")
        manager.who_is_here(self.name)

    @action_handlers.handler("LOGOUT")
    @asyncio.coroutine
    def handle_logout(self, _, manager):
        self.debug_print("{name}: Logging out\n")
        raise Logout

    @asyncio.coroutine
    def read_and_send(self, manager, recipients=None):
        '''
        Read a body and send to a list of recipients. If the recipients list is
        None, broadcast.
        '''
        # Get the first body header line
        line = yield from self.reader.readline()

        # Parse body header line
        match = body_pattern.match(line.decode('ascii'))
        if match is None:
            raise LineError("Malformed body header", line)

        body_parts = [line]

        # Read body
        if match.lastgroup == 'short_size':
            # Get body size
            size = int(match.group('short_size'))

            # Read body
            body = yield from self.reader.readexactly(size)
            body_parts.append(body)

        elif match.lastgroup == 'chunk_size':
            while True:
                # Get chunk size
                size = int(match.group('chunk_size'))

                # Break on chunk size of 0
                if size == 0:
                    break

                # Read chunk
                chunk = yield from self.reader.readexactly(size)
                body_parts.append(chunk)

                # Get next chunk line
                line = yield from self.reader.readline()
                match = chunk_pattern.match(line.decode('ascii'))
                if match is None:
                    raise LineError("Malformed chunk header", line)

                # Add chunk line to body
                body_parts.append(line)
        else:
            raise ServerError()

        manager.send_to_recipients(self.name, recipients, body_parts)

    @common.consumer
    def message_sender(self, randoms, random_rate):
        '''
        Consumer-generator to handle sending messages to this client. Primarily
        responsible for also injecting random bonus messages
        '''
        # If we're using randoms
        if randoms and random_rate > 0:
            while True:
                # set would be better, but random.choice needs a sequence
                recent_senders = list()

                # Perform random_rate normal writes, then a random write
                for _ in range(random_rate):
                    sender, body = yield
                    recent_senders.append(sender)
                    self.writer.write(body)

                self.writer.writelines((
                    common.make_sender_line(random.choice(recent_senders)),
                    random.choice(randoms)))
        else:
            while True:
                _, body = yield
                self.writer.write(body)
