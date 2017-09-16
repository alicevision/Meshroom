
import processGraph as pg

import os
import sys
import re
import argparse


parser = argparse.ArgumentParser(description='Create a new Node Type')
parser.add_argument('node', metavar='NodeName', type=str,
                    help='New node name')

args = parser.parse_args()

if sys.stdin.isatty():
    print('No input documentation.')
    print('Usage: YOUR_COMMAND --help | {cmd} YourCommand'.format(cmd=os.path.splitext(__file__)[0]))
    exit(-1)

inputDoc = [line for line in sys.stdin]
inputArgs = [line for line in inputDoc if '--' in line]

arg_re = re.compile('.*?--(?P<longName>\w+).*?')


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

for inputArg in inputArgs:
    paramName = arg_re.match(inputArg).group('longName')

    inputArgLower = inputArg.lower()
    isFile = 'path' in inputArgLower or 'folder' in inputArgLower or 'file' in inputArgLower
    outputNodeStr += '''
    {name} = pg.{attributeType}(
            label='{label}',
            uid=[0],
            )'''.format(name=paramName, label=convertToLabel(paramName), attributeType='FileAttribute' if isFile else 'ParamAttribute')


print(outputNodeStr)