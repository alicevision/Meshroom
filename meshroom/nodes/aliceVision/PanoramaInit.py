__version__ = "2.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class PanoramaInit(desc.AVCommandLineNode):
    commandLine = 'aliceVision_panoramaInit {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Panorama HDR'
    documentation = '''
This node allows to setup the Panorama:

1/ Enables the initialization the cameras from known position in an XML file (provided by
["Roundshot VR Drive"](https://www.roundshot.com/xml_1/internet/fr/application/d394/d395/f396.cfm) ).

2/ Enables to setup Full Fisheye Optics (to use an Equirectangular camera model).

3/ To automatically detects the Fisheye Circle (radius + center) in input images or manually adjust it.

'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.ChoiceParam(
            name="initializeCameras",
            label="Initialize Cameras",
            description="Initialize cameras.",
            value="No",
            values=["No", "File", "Horizontal", "Horizontal+Zenith", "Zenith+Horizontal", "Spherical"],
        ),
        desc.File(
            name="config",
            label="XML Config",
            description="XML data file.",
            value="",
            enabled=lambda node: node.initializeCameras.value == "File",
        ),
        desc.BoolParam(
            name="yawCW",
            label="Yaw CW",
            description="If selected, the yaw rotation will be clockwise. Otherwise, it will be counter-clockwise.",
            value=True,
            enabled=lambda node: ("Horizontal" in node.initializeCameras.value) or (node.initializeCameras.value == "Spherical"),
        ),
        desc.BoolParam(
            name="buildContactSheet",
            label="Build Contact Sheet",
            description="Build the contact sheet for the panorama if an XML data file is provided.\n"
                        "The contact sheet consists in a preview of the panorama using the input images.",
            value=True,
            enabled=lambda node: node.config.enabled and node.config.value != "",
        ),
        desc.ListAttribute(
            elementDesc=desc.IntParam(
                name="nbViews",
                label="Number of Views",
                description="Number of views for a line.",
                value=-1,
                range=(-1, 20, 1),
            ),
            name="nbViewsPerLine",
            label="Spherical: Nb Views Per Line",
            description="Number of views per line in Spherical acquisition.\n"
                        "Assumes angles from [-90,+90deg] for pitch and [-180,+180deg] for yaw.\n"
                        "Use -1 to estimate the number of images automatically.",
            joinChar=",",
            enabled=lambda node: node.initializeCameras.value == "Spherical",
        ),
        desc.BoolParam(
            name="useFisheye",
            label="Full Fisheye",
            description="Set this option to declare a full fisheye panorama setup.",
            value=False,
        ),
        desc.BoolParam(
            name="estimateFisheyeCircle",
            label="Estimate Fisheye Circle",
            description="Automatically estimate the fisheye circle center and radius instead of using user values.",
            value=True,
            enabled=lambda node: node.useFisheye.value,
        ),
        desc.GroupAttribute(
            name="fisheyeCenterOffset",
            label="Fisheye Center",
            description="Center of the fisheye circle (XY offset to the center in pixels).",
            groupDesc=[
                desc.FloatParam(
                    name="fisheyeCenterOffset_x",
                    label="x",
                    description="X offset in pixels.",
                    value=0.0,
                    range=(-1000.0, 10000.0, 1.0),
                ),
                desc.FloatParam(
                    name="fisheyeCenterOffset_y",
                    label="y",
                    description="Y offset in pixels.",
                    value=0.0,
                    range=(-1000.0, 10000.0, 1.0),
                ),
            ],
            group=None,  # skip group from command line
            enabled=lambda node: node.useFisheye.value and not node.estimateFisheyeCircle.value,
        ),
        desc.FloatParam(
            name="fisheyeRadius",
            label="Fisheye Radius",
            description="Fisheye visibillity circle radius (in % of image's shortest side).",
            value=96.0,
            range=(0.0, 150.0, 0.01),
            enabled=lambda node: node.useFisheye.value and not node.estimateFisheyeCircle.value,
        ),
        desc.ChoiceParam(
            name="inputAngle",
            label="Input Angle Offset",
            description="Add a rotation to the input XML given poses (CCW).",
            value="None",
            values=["None", "rotate90", "rotate180", "rotate270"],
        ),
        desc.BoolParam(
            name="debugFisheyeCircleEstimation",
            label="Debug Fisheye Circle Detection",
            description="Debug fisheye circle detection.",
            value=False,
            enabled=lambda node: node.useFisheye.value,
            advanced=True,
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    outputs = [
        desc.File(
            name="contactSheet",
            label="Contact sheet",
            semantic="image",
            description="Contact sheet path.",
            value=desc.Node.internalFolder + "contactSheetImage.jpg",
            group="",  # do not export on the command line
            enabled=lambda node: node.buildContactSheet.enabled
        ),
        desc.File(
            name="outSfMData",
            label="SfMData File",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfmData.sfm",
        ),
    ]
