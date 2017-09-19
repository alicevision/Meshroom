#!/usr/bin/env python3
from __future__ import print_function

import argparse
import os
import re
import sys


def trim(s):
    '''
    All repetition of any kind of space is replaced by a single space
    and remove trailing space at beginning or end.
    '''
    # regex to replace all space groups by a single space
    # use split() to remove trailing space at beginning/end
    return re.sub('\s+', ' ', s).strip()

def quotesForStrings(valueStr):
    '''
    Return the input string with quotes if it cannot be cast into another builtin type.
    '''
    v = valueStr
    try:
        int(valueStr)
    except ValueError:
        try:
            float(valueStr)
        except ValueError:
            v = "'{}'".format(valueStr)
    return v


parser = argparse.ArgumentParser(description='Create a new Node Type')
parser.add_argument('node', metavar='NodeName', type=str,
                    help='New node name')
parser.add_argument('--output', metavar='DIR', type=str,
                    default=os.path.dirname(__file__),
                    help='Output plugin folder')
parser.add_argument('--parser', metavar='PARSER', type=str,
                    default='boost',
                    help='Select the parser adapted for your command line: {boost,cmdLineLib,basic}.')
parser.add_argument("--force", help="Allows to ovewrite the output plugin file.",
                    action="store_true")

args = parser.parse_args()

if sys.stdin.isatty():
    print('No input documentation.')
    print('Usage: YOUR_COMMAND --help | {cmd} YourCommand'.format(cmd=os.path.splitext(__file__)[0]))
    exit(-1)

inputCmdLineDoc = ''.join([line for line in sys.stdin])

def convertToLabel(name):
    camelCaseToLabel = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
    snakeToLabel = ' '.join(word.capitalize() for word in camelCaseToLabel.split('_'))
    snakeToLabel = ' '.join(word.capitalize() for word in snakeToLabel.split(' '))
    # print name, camelCaseToLabel, snakeToLabel
    return snakeToLabel


outputNodeStr = '''
import processGraph as pg

class __COMMANDNAME__(pg.CommandLineNodeDesc):
    internalFolder = '{nodeType}/{uid0}/'
    cmdLineExpr = '{nodeType} {allParams}'
'''.replace('__COMMANDNAME__', 'args.node')


print(inputCmdLineDoc)

args_re = None
if args.parser == 'boost':
    args_re = re.compile(
        '^\s+' # space(s)
        '\[?\s*' # potential '['
        '(?:-(?P<argShortName>\w+)\|?)?' # potential argument short name
        '\s*\[?' # potential '['
        '\s*--(?P<argLongName>\w+)' # argument long name
        '(?:\s*\])?' # potential ']'
        '(?:\s+(?P<arg>\w+)?)?' # potential arg
        '(?:\s+\(\=(?P<defaultValue>\w+)\))?' # potential default value
        '\s+(?P<descriptionFirst>.*?)\n' # end of the line
        '(?P<descriptionNext>(?:\s+[^-\s].+?\n)*)' # next documentation lines
        , re.MULTILINE)
elif args.parser == 'cmdLineLib':
    args_re = re.compile(
        '^'
        '\[' # '['
        '\s*'
        '-(?P<argShortName>\w+)' # argument short name
        '\|'
        '--(?P<argLongName>\w+)' # argument long name
        '\]' # ']'
        '()' # no arg
        '()' # no default value
        '\s+(?P<descriptionFirst>.*?)\n' # end of the line
        '(?P<descriptionNext>(?:\s+[^\[\s].+?\n)*)' # next documentation lines
        , re.MULTILINE)
elif args.parser == 'basic':
    args_re = re.compile('()--(?P<argLongName>\w+)()()()()')
else:
    print('Error: Unknown input parser "{}"'.format(args.parser))
    exit(-1)

inputArgs = args_re.findall(inputCmdLineDoc)

print('='*80)

for inputArg in inputArgs:
    shortName = inputArg[0]
    longName = longName = inputArg[1]
    arg = inputArg[2]
    value = inputArg[3]
    description = trim(''.join(inputArg[4:]))

    inputArgLower = ' '.join(inputArg).lower()
    isFile = 'path' in inputArgLower or 'folder' in inputArgLower or 'file' in inputArgLower
    outputNodeStr += '''
    {name} = pg.{attributeType}(
            label='{label}',
            description='{description}',
            value={value},
            shortName='{shortName}',
            arg='{arg}',
            uid=[0],
            )'''.format(
                name=longName,
                attributeType='FileAttribute' if isFile else 'ParamAttribute',
                label=convertToLabel(longName),
                description=description,
                value=quotesForStrings(value),
                shortName=shortName,
                arg=arg,
                )

outputFilepath = os.path.join(args.output, args.node + '.py')

if not args.force and os.path.exists(outputFilepath):
    print('Plugin "{}" already exists "{}".'.format(args.node, outputFilepath))
    exit(-1)

with open(outputFilepath, 'w') as pluginFile:
    pluginFile.write(outputNodeStr)

print('New node exported to: "{}"'.format(outputFilepath))
