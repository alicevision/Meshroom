import inspect
import os


class Attribute:
    '''
    '''
    isOutput = False
    uid = []
    group = 'allParams'
    commandLine = '{nodeType} --help' # need to be overridden
    def __init__(self):
        pass


class FileAttribute(Attribute):
    '''
    '''
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class ParamAttribute(Attribute):
    '''
    '''
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Node:
    '''
    '''
    internalFolder = '{nodeType}/{uid0}/'

    def __init__(self):
        pass


class CommandLineNode(Node):
    '''
    '''
    def __init__(self):
        pass
