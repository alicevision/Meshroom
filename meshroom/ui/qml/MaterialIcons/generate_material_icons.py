import argparse
import os

parser = argparse.ArgumentParser(description='Generate a MaterialIcons.qml singleton from codepoints file.\n'
                                'An example of codepoints file for MaterialIcons: https://github.com/google/material-design-icons/blob/master/font/MaterialIcons-Regular.codepoints.')
parser.add_argument('codepoints', type=str, help='Codepoints file.')
parser.add_argument('--output', type=str, default='.', help='')

args = parser.parse_args()

# Override icons with problematic names
mapping = {
    'delete': 'delete_',
    'class': 'class_',
    '3d_rotation': '_3d_rotation',
    'opacity': 'opacity_',
    'transform': 'transform_',
    'print': 'print_',
    'public': 'public_',
    'password': 'pwd',
    'wifi_password': 'wifi_pwd',
    'try': 'try_'
}

# Override icons that are numeric literals
numeric_literals = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

# List of existing name to override potential duplicates
names = []

with open(os.path.join(args.output, 'MaterialIcons.qml'), 'w') as qml_file:
    qml_file.write('pragma Singleton\n')
    qml_file.write('import QtQuick 2.15\n\n')
    qml_file.write('QtObject {\n')
    qml_file.write('    property FontLoader fl: FontLoader {\n')
    qml_file.write('        source: "./MaterialIcons-Regular.ttf"\n')
    qml_file.write('    }\n')
    qml_file.write('    readonly property string fontFamily: fl.name\n\n')

    with open(args.codepoints, 'r') as codepoints:
        for line in codepoints.readlines():
            name, code = line.strip().split(" ")
            name = mapping.get(name, name)

            # Add underscore to names that are numeric literals (e.g. "123" will become "_123")
            if name[0] in numeric_literals:
                name = "_" + name

            # If the name already exists in the list, append an index
            if name in names:
                index = 2
                while name + str(index) in names:
                    index = index + 1
                name = name + str(index)

            names.append(name)
            qml_file.write('    readonly property string {}: "\\u{}"\n'.format(name, code))
        qml_file.write('}\n')
