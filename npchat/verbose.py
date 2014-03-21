'''
Created on Mar 21, 2014

@author: nathan

Classes that handle formatting of verbose input and output. Because the server
was implemented before thinking about how to do verbose input and output, we
instead cache lines read and written, and print them on demand.
'''

import asyncio
from sys import stdout


class VerbosePrinter:
    def __init__(self, ip):
        self.cache = []
        self.ip = ip
        self.name = None

    def get_peer_name(self):
        if self.name is None:
            return self.ip
        else:
            return "{self.name} ({self.ip})".format(self=self)

    def generic_print_cached(self, file, direction):
        data = (b''.join(self.cache)
            .decode('ascii')
            .replace('\n', "\\n\n")
            .rstrip())
        if data.find('\n', 0, -1) != -1:
            data = ''.join('\n  {line}'.format(line=line)
                             for line in data.splitlines())

        print("{direction} {name}: {body}".format(
            direction=direction, name=self.get_peer_name(), body=data),
            file=file)

        self.cache = []


class VerboseWriter(VerbosePrinter):
    def __init__(self, ip, writer):
        VerbosePrinter.__init__(self, ip)
        self.writer = writer

    def write(self, data):
        self.cache.append(data)
        self.writer.write(data)

    def writelines(self, data):
        data = tuple(data)
        self.cache.extend(data)
        self.writer.writelines(data)

    def close(self):
        self.cache = []
        self.writer.close()

    def print_cached(self, file=stdout):
        self.generic_print_cached(file, "SENT to")

    def print_cached_random(self, file=stdout):
        self.generic_print_cached(file, "SENT (randomly!) TO")


class VerboseReader(VerbosePrinter):
    def __init__(self, ip, reader):
        VerbosePrinter.__init__(self, ip)
        self.reader = reader

    @asyncio.coroutine
    def readline(self):
        line = yield from self.reader.readline()
        self.cache.append(line)
        return line

    @asyncio.coroutine
    def readexactly(self, n):
        data = yield from self.reader.readexactly(n)
        self.cache.append(data)
        return data

    def print_cached(self, file=stdout):
        self.generic_print_cached(file, "RCVD from")


def make_verbose_reader_writer(reader, writer):
    ip = writer.get_extra_info('peername')[0]
    return VerboseReader(ip, reader), VerboseWriter(ip, writer)
