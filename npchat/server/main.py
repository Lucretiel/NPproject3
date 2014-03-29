'''
Created on Mar 24, 2014

@author: nathan
'''

'''
Created on Mar 17, 2014

@author: nathan
'''

import asyncio
from argparse import ArgumentParser
from npchat.server.manager import ChatManager

# TODO: more
default_randoms = (
    "Hey, you're kinda hot",
    "No way!",
    "I like Justin Bieber....a lot",
    "You butt",
    "GOOD",
    "I'm not touching yours, I'm only touching mine",
    "I want you to lose so hard you go inactive",
    "Philadelphia is the worst state in the world",
    "BIG\tBLACK\tDICK",
    "i'm all about three things, getting money, getting pussy, and the dewey "
        "decimal system",
    "where is your shit you butt")


def main():
    parser = ArgumentParser(
        description="Network Programming Project 3: Chat Server")

    parser.add_argument('-v', "--verbose", action='store_true',
        help="Enable standard verbose output")
    parser.add_argument('-d', "--debug", action='store_true',
        help="Print additional status messages")
    parser.add_argument('-e', "--extra", action='append', dest='randoms',
        help="Additional random phrases to inject", metavar='MESSAGE',
        default=[])
    parser.add_argument('-r', '--rate', type=int, default=3,
        help="How many normal messages to send between random messages "
        "(default: 3)", dest='random_rate')
    parser.add_argument('-E', '--exclude', action='store_false',
        help="Exclude the build-in random messages", dest='use_default')
    parser.add_argument('-m', '--multiverse', action='store_true',
        help="Make each port a seperate chat universe")
    parser.add_argument("ports", nargs='+', type=int, metavar='PORT',
        help="TCP/UDP port(s) to listen on")

    args = parser.parse_args()
    if args.use_default:
        args.randoms.extend(default_randoms)

    run_forever = asyncio.get_event_loop().run_until_complete

    if args.multiverse:
        run_forever(asyncio.wait([ChatManager(args.randoms, args.random_rate,
            args.verbose, args.debug).serve_forever(port)
            for port in args.ports]))
    else:
        run_forever(ChatManager(args.randoms, args.random_rate, args.verbose,
            args.debug).serve_forever_multi(args.ports))

if __name__ == '__main__':
    main()
