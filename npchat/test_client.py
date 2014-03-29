'''
Created on Mar 28, 2014

@author: nathan
'''

import asyncio
import random
import argparse

from npchat import common
from time import time


@asyncio.coroutine
def test_npchat_reader(name, reader):
    @asyncio.coroutine
    def readline():
        line = yield from reader.readline()
        return line.decode('ascii').rstrip()

    @asyncio.coroutine
    def readbody(n):
        body = yield from reader.readexactly(n)
        return body.decode('ascii')

    ok = yield from readline()
    if ok != 'OK':
        raise RuntimeError('OK line')
    else:
        print("Logged in {name}".format(name=name))

    while True:
        # Get from line
        from_line = yield from readline()
        if not from_line:
            break
        from_user = from_line.split()[1]
        print("From {user}:".format(user=from_user))

        # Get body
        size = yield from readline()
        if size.startswith('C'):
            body = []
            while size != 'C0':
                body_part = yield from readbody(int(size[1:]))
                body.append(body_part)
                size = yield from readline()
            body = ''.join(body)
        else:
            body = yield from readbody(int(size))

        body = '\n'.join('  ' + line.rstrip() for line in body.split('\n'))
        print(body)


@asyncio.coroutine
def test_npchat_devnull(reader):
    '''
    CONSUME ALL INPUT AND THROW IT INTO THE VOID

    CONSUME

    CONSUUUUUUUUME
    '''

    # Read kilobyte chunks forever
    body = yield from reader.read(1024)
    while body:
        body = yield from reader.reader(1024)


@asyncio.coroutine
def test_npchat(username, messages, host, port, do_output, alive):
    print("Connecting {username} on port {port}".format(
        username=username, port=port))

    # Connect to chat server
    reader, writer = yield from asyncio.open_connection(host, port)

    if do_output:
        reader_task = asyncio.Task(test_npchat_reader(username, reader))
    else:
        reader_task = asyncio.Task(test_npchat_devnull(reader))

    # Login
    writer.write("ME IS {username}\n"
        .format(username=username)
        .encode('ascii'))

    # Wait 1 second before sending messages
    yield from asyncio.sleep(1)

    # Run for 30-60 seconds
    if alive:
        end = time() + random.uniform(*alive)
    else:
        end = float('inf')

    while time() < end:
        # Wait 1-5 seconds
        yield from asyncio.sleep(random.uniform(1, 5))

        action = random.randrange(2)

        # TODO: Send
        # BROADCAST
        if action == 0:
            writer.write('BROADCAST {name}\n'
                .format(name=username).encode('ascii'))
            writer.writelines(common.make_body(random.choice(messages)))
        elif action == 1:
            writer.write('WHO HERE {name}\n'
                .format(name=username).encode('ascii'))

    # Wait 1 final second, then logout
    yield from asyncio.sleep(1)
    writer.write('LOGOUT {name}\n'.format(name=username).encode('ascii'))

    asyncio.wait(reader_task, None)


def main():
    parser = argparse.ArgumentParser("NPchat testing client")

    parser.add_argument("-u", "--users", metavar='USERNAME', nargs='+',
        help="Specific username(s) to add", default=[])
    parser.add_argument("-e", "--extra", type=int, default=32,
        metavar='N', help="Number of extra numberd usernames to add")
    parser.add_argument("-m", "--messages", dest='messages', nargs='+',
        metavar='MESSAGE', help="Extra messages to broadcast", default=[])
    parser.add_argument("-a", "--alive", nargs=2, default=None, type=float,
        metavar="TIME", help="Seconds in which each chatter will be alive")
    parser.add_argument("host", metavar='HOST')
    parser.add_argument("ports", metavar='PORT', nargs='+', type=int)

    args = parser.parse_args()

    usernames = args.users + list(range(args.extra))
    if not usernames:
        raise RuntimeError("Need some users to exchange messages")

    messages = [
        "Hello World!",
        "Goodbye, World!",
        "I AM THE BEST",
        "Here is another message",
        "Here is\na mutliline\nmessage",

        # No commas
        "Here is a very very very long message\n"
        "It has more than 100 characters,\n"
        "So it will have to be sent via a chunked\n"
        "encoding."] + args.messages

    tasks = [test_npchat(usernames[0], messages, args.host,
        random.choice(args.ports), True, args.alive)]
    tasks.extend(test_npchat(name, messages, args.host,
            random.choice(args.ports), False, args.alive)
        for name in usernames[1:])

    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))

if __name__ == '__main__':
    main()
