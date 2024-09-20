__version__ = "1.1"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class MeshMasking(desc.AVCommandLineNode):
    commandLine = 'aliceVision_meshMasking {allParams}'
    category = 'Mesh Post-Processing'
    documentation = '''
Decimate triangles based on image masks.
'''

    inputs = [
        desc.File(
            name="input",
            label="Dense SfMData",
            description="Dense SfMData file.",
            value="",
        ),
        desc.File(
            name="inputMesh",
            label="Input Mesh",
            description="Input mesh.",
            value="",
        ),
        desc.ChoiceParam(
            name="outputMeshFileType",
            label="Output Mesh Type",
            description="File type of the output mesh.",
            value="obj",
            values=["obj", "gltf", "fbx", "stl"],
            group="",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="masksFolder",
                label="Masks Folder",
                description="Folder containing some masks.",
                value="",
            ),
            name="masksFolders",
            label="Masks Folders",
            description="Use masks from specific folder(s). Filename should be the same or the image UID.",
        ),
        desc.ChoiceParam(
            name="maskExtension",
            label="Mask Extension",
            description="File extension for the masks to use.",
            value="png",
            values=["exr", "jpg", "png"],
        ),
        desc.IntParam(
            name="threshold",
            label="Threshold",
            description="The minimum number of visibilities to keep a vertex.",
            value=1,
            range=(1, 100, 1),
        ),
        desc.BoolParam(
            name="smoothBoundary",
            label="Smooth Boundary",
            description="Modify the triangles at the boundary to fit the masks.",
            value=False,
        ),
        desc.BoolParam(
            name="invert",
            label="Invert",
            description="If ticked, the selected area is ignored.\n"
                        "If not, only the selected area is considered.",
            value=False,
        ),
        desc.BoolParam(
            name="undistortMasks",
            label="Undistort Masks",
            description="Undistort the masks with the same parameters as the matching image.\n"
                        "Select it if the masks are drawn on the original images.",
            value=False,
        ),
        desc.BoolParam(
            name="usePointsVisibilities",
            label="Use Points visibilities",
            description="Use the points visibilities from the meshing to filter triangles.\n"
                        "Example: when they are occluded, back-face, etc.",
            value=False,
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
            name="outputMesh",
            label="Mesh",
            description="Output mesh file.",
            value=desc.Node.internalFolder + "mesh.{outputMeshFileTypeValue}",
        ),
    ]
