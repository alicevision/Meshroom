__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaInit(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaInit {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
            value='',
            uid=[0],
        ),
        desc.File(
            name='config',
            label='Xml Config',
            description="XML Data File",
            value='',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name='dependency',
                label='',
                description="",
                value='',
                uid=[],
            ),
            name='dependency',
            label='Dependency',
            description="Folder(s) in which computed features are stored. (WORKAROUND for valid Tractor graph submission)",
            group='forDependencyOnly',  # not a command line argument
        ),
        desc.BoolParam(
            name='useFisheye',
            label='Full Fisheye',
            description='To declare a full fisheye panorama setup',
            value=False,
            uid=[0],
        ),
        desc.GroupAttribute(
            name="fisheyeCenterOffset",
            label="Fisheye Center",
            description="Center of the Fisheye circle (XY offset to the center in pixels).",
            groupDesc=[
                desc.FloatParam(
                    name="x", label="x", description="",
                    value=0.0,
                    uid=[0],
                    range=(-1000.0, 10000.0, 1.0)),
                desc.FloatParam(
                    name="y", label="y", description="",
                    value=0.0,
                    uid=[0],
                    range=(-1000.0, 10000.0, 1.0)),
                ],
        ),
        desc.FloatParam(
            name='fisheyeRadius',
            label='Radius',
            description='Fisheye visibillity circle radius (% of image shortest side).',
            value=96.0,
            range=(0.0, 150.0, 0.01),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='Verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='outSfMDataFilename',
            label='Output SfMData File',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'sfmData.sfm',
            uid=[],
        )
    ]
