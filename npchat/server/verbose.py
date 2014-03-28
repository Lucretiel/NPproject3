'''
Created on Mar 26, 2014

@author: nathan

These classes wrap the standard reader and writer, to verbosly print data read
or written
'''

import asyncio


class VerboseStream:
    def __init__(self, ip, port):
        self.location = "{ip}:{port}".format(ip=ip, port=port)
        self.name = None
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, name):
        self._name = name
        if what is None:
            header = "{self.prefix} {self.location}:"
        else:
            header = "{self.prefix} {self.name} ({self.location}):"
        self.header = header.format(self=self)

    def print_thing(self, thing):
        #Set prefix in derived class
        print(self.header)
        for line in thing.decode('ascii').rstrip().split('\n'):
            print(' ', line)


class VerboseReader(VerboseStream):
    prefix = "RCVD from"

    def __init__(self, reader, ip, port):
        VerboseStream.__init__(self, ip, port)
        self.reader = reader

    @asyncio.coroutine
    def readline(self):
        line = yield from self.reader.readline()
        self.print_thing(line)
        return line

    @asyncio.coroutine
    def readexactly(self, n):
        body = yield from self.reader.readexactly(n)
        self.print_thing(body)

        return body


class VerboseWriter(VerboseStream):
    prefix = "SENT to"

    def __init__(self, writer, ip, port):
        VerboseStream.__init__(self, ip, port)
        self.writer = writer

    def write(self, body):
        self.print_thing(body)
        self.writer.write(body)

    def writelines(self, lines):
        # It'd be nice to do writer.writelines, but why bother?
        self.write(b''.join(lines))

    def close(self):
        self.writer.close()


def make_verbose_reader_writer(reader, writer):
    ip, port = writer.get_extra_info('peername')
    return VerboseReader(reader, ip, port), VerboseWriter(writer, ip, port)

