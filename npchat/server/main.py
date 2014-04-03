'''
Created on Mar 17, 2014

@author: nathan
'''

from argparse import ArgumentParser
import asyncio

from npchat.server.manager import ChatManager


default_randoms = (
    "Hey, you're kinda hot",
    "No way!",
    "I like Justin Bieber....a lot",
    "You butt",
    "GOOD",
    "I'm not touching yours, I'm only touching mine",
    "I want you to lose so hard you go inactive",
    "Philadelphia is the worst state in the world",
    "You startled my cat",
    "Sweet potato rolls are the best rolls"
    )


def main():
    parser = ArgumentParser(
        description="Network Programming Project 3: Chat Server")

    parser.add_argument('-v', "--verbose", action='store_true',
        help="Enable standard verbose output")
    parser.add_argument('-d', "--debug", action='store_true',
        help="Print additional status messages")
    parser.add_argument('-e', "--extra", nargs='+', dest='randoms',
        help="Additional random phrases to inject", metavar='MESSAGE',
        default=[])
    parser.add_argument('-r', '--rate', type=int, default=3,
        help="How many normal messages to send between random messages "
        "(default: 3)", dest='random_rate')
    parser.add_argument('-E', '--exclude', action='store_false',
        help="Exclude the build-in random messages", dest='use_default')
    parser.add_argument('-m', '--multiverse', action='store_true',
        help="Make each port a seperate chat universe")
    parser.add_argument('-t', '--timeout', type=int, default=60,
        help="Amount of time to wait for a read before disconnecting")
    parser.add_argument("ports", nargs='+', type=int, metavar='PORT',
        help="TCP/UDP port(s) to listen on")

    args = parser.parse_args()
    if args.use_default:
        args.randoms.extend(default_randoms)

    if args.multiverse:
        # Each port is its own manager
        tasks = [ChatManager(args.randoms, args.random_rate, args.verbose,
            args.debug, args.timeout).serve_forever(port)
            for port in args.ports]
    else:
        # One manager to rule them all
        manager = ChatManager(args.randoms, args.random_rate, args.verbose,
            args.debug, args.timeout)
        tasks = [manager.serve_forever(port) for port in args.ports]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.run_forever()

if __name__ == '__main__':
    main()
