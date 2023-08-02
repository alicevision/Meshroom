__version__ = "1.0"

from meshroom.core import desc
import os.path

currentDir = os.path.dirname(os.path.abspath(__file__))

class ScenePreview(desc.CommandLineNode):
    commandLine = '{blenderCmdValue} -b --python {scriptValue} -- {allParams}'
    size = desc.DynamicNodeSize('cameras')
    parallelization = desc.Parallelization(blockSize=40)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Utils'
    documentation = '''
This node uses Blender to visualize a 3D model from a given set of cameras.
The cameras must be a SfMData file in JSON format.
For the 3D model it supports both point clouds in Alembic format and meshes in OBJ format.
One frame per viewpoint will be rendered, and the undistorted views can optionally be used as background.
'''

    inputs = [
        desc.File(
            name="blenderCmd",
            label="Blender Command",
            description="Command to launch Blender.",
            value="blender",
            uid=[],
            group="",
        ),
        desc.File(
            name="script",
            label="Script",
            description="Path to the internal script for rendering in Blender.",
            value=os.path.join(currentDir, "scripts", "preview.py"),
            uid=[],
            group="",
            advanced=True,
        ),
        desc.File(
            name="cameras",
            label="Cameras",
            description="SfMData with the views, poses and intrinsics to use (in JSON format).",
            value="",
            uid=[0],
        ),
        desc.File(
            name="model",
            label="Model",
            description="Point cloud (.abc) or mesh (.obj) to render.",
            value="",
            uid=[0],
        ),
        desc.BoolParam(
            name="useBackground",
            label="Display Background",
            description="Use the undistorted images as background.",
            value=True,
            uid=[0],
        ),
        desc.File(
            name="undistortedImages",
            label="Undistorted Images",
            description="Folder containing the undistorted images.",
            value="",
            uid=[0],
            enabled=lambda node: node.useBackground.value,
        ),
        desc.GroupAttribute(
            name="pointCloudParams",
            label="Point Cloud Settings",
            group=None,
            enabled=lambda node: node.model.value.lower().endswith(".abc"),
            description="Settings for point cloud rendering.",
            groupDesc=[
                desc.FloatParam(
                    name="particleSize",
                    label="Particle Size",
                    description="Scale of particles used for the point cloud.",
                    value=0.01,
                    range=(0.01, 1.0, 0.01),
                    uid=[0],
                ),
                desc.ChoiceParam(
                    name="particleColor",
                    label="Particle Color",
                    description="Color of particles used for the point cloud.",
                    value="Red",
                    values=["Grey", "White", "Red", "Green", "Magenta"],
                    exclusive=True,
                    uid=[0],
                ),
            ]
        ),
        desc.GroupAttribute(
            name="meshParams",
            label="Mesh Settings",
            group=None,
            enabled=lambda node: node.model.value.lower().endswith(".obj"),
            description="Setting for mesh rendering.",
            groupDesc=[
                desc.ChoiceParam(
                    name="shading",
                    label="Shading",
                    description="Shading method for visualizing the mesh.",
                    value="wireframe",
                    values=["wireframe", "line_art"],
                    exclusive=True,
                    uid=[0],
                ),
                desc.ChoiceParam(
                    name="edgeColor",
                    label="Edge Color",
                    description="Color of the mesh edges.",
                    value="Red",
                    values=["Grey", "White", "Red", "Green", "Magenta"],
                    exclusive=True,
                    uid=[0],
                ),
            ]
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Output folder.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name="frames",
            label="Frames",
            description="Frames rendered in Blender.",
            semantic="image",
            value=desc.Node.internalFolder + "<FILENAME>_preview.jpg",
            uid=[],
            group="",
        ),
    ]
