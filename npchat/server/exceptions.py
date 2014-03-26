'''
Created on Mar 24, 2014

@author: nathan
'''


class ChatError(RuntimeError):
    @property
    def message(self):
        return self.args[0]


class LineError(ChatError):
    '''
    Error with the line. Usually means a parse or unknown command error.
    '''
    @property
    def message(self):
        return "{error}: {line}".format(
            error=self.args[0], line=self.args[1].decode('ascii'))


class ServerError(ChatError):
    @property
    def message(self):
        return 'UNKNOWN SERVER ERROR'
