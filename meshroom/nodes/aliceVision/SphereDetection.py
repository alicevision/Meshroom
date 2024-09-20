__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class SphereDetection(desc.CommandLineNode):
    commandLine = 'aliceVision_sphereDetection {allParams}'
    category = 'Photometric Stereo'
    documentation = '''
Detect spheres in pictures. These spheres will be used for lighting calibration.
Spheres can be automatically detected or manually defined in the interface.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="modelPath",
            label="Detection Network",
            description="Deep learning network for automatic calibration sphere detection.",
            value="${ALICEVISION_SPHERE_DETECTION_MODEL}",
        ),
        desc.BoolParam(
            name="autoDetect",
            label="Automatic Sphere Detection",
            description="Automatic detection of calibration spheres.",
            value=False,
        ),
        desc.FloatParam(
            name="minScore",
            label="Minimum Score",
            description="Minimum score for the detection.",
            value=0.0,
            range=(0.0, 50.0, 0.01),
            advanced=True,
        ),
        desc.GroupAttribute(
            name="sphereCenter",
            label="Sphere Center",
            description="Center of the circle (XY offset to the center of the image in pixels).",
            groupDesc=[
                desc.FloatParam(
                    name="x",
                    label="x",
                    description="X offset in pixels.",
                    value=0.0,
                    range=(-1000.0, 10000.0, 1.0),
                ),
                desc.FloatParam(
                    name="y",
                    label="y",
                    description="Y offset in pixels.",
                    value=0.0,
                    range=(-1000.0, 10000.0, 1.0),
                ),
            ],
            enabled=lambda node: not node.autoDetect.value,
            group=None,  # skip group from command line
        ),
        desc.FloatParam(
            name="sphereRadius",
            label="Radius",
            description="Sphere radius in pixels.",
            value=500.0,
            range=(0.0, 10000.0, 0.1),
            enabled=lambda node: not node.autoDetect.value,
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
            name="output",
            label="Output Path",
            description="Sphere detection information will be written here.",
            value=desc.Node.internalFolder + "/detection.json",
        )
    ]
