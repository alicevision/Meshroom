__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

class PhotometricStereo(desc.CommandLineNode):
    commandLine = 'aliceVision_photometricStereo {allParams}'
    category = 'Photometric Stereo'
    documentation = '''
Reconstruction using Photometric Stereo. A normal map is evaluated from several photographs taken from the same point of view, but under different lighting conditions.
The lighting conditions are assumed to be known.
'''

    inputs = [
        desc.File(
            name="inputPath",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="pathToJSONLightFile",
            label="Light File",
            description="Path to a JSON file containing the lighting information.\n"
                        "If empty, .txt files are expected in the image folder.",
            value="defaultJSON.txt",
        ),
        desc.File(
            name="maskPath",
            label="Mask Folder Path",
            description="Path to a folder containing masks or to a mask directly.",
            value="",
        ),
        desc.ChoiceParam(
            name="SHOrder",
            label="Spherical Harmonics Order",
            description="Order of the spherical harmonics:\n"
                        " - 0: directional.\n"
                        " - 1: directional + ambient.\n"
                        " - 2: second order spherical harmonics.",
            values=["0", "1", "2"],
            value="0",
            advanced=True,
        ),
        desc.BoolParam(
            name="removeAmbient",
            label="Remove Ambient Light",
            description="True if the ambient light is to be removed on the PS images, false otherwise.",
            value=False,
            advanced=True,
        ),
        desc.BoolParam(
            name="isRobust",
            label="Use Robust Algorithm",
            description="True to use the robust algorithm, false otherwise.",
            value=False,
            advanced=True,
        ),
        desc.IntParam(
            name="downscale",
            label="Downscale Factor",
            description="Downscale factor for faster results.",
            value=1,
            range=(1, 10, 1),
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
            name="outputPath",
            label="Output Folder",
            description="Path to the output folder.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="outputSfmDataAlbedo",
            label="SfMData Albedo",
            description="Output SfMData file containing the albedo information.",
            value=desc.Node.internalFolder + "/albedoMaps.sfm",
            group="",  # remove from command line
        ),
        desc.File(
            name="outputSfmDataNormal",
            label="SfMData Normal",
            description="Output SfMData file containing the normal maps information.",
            value=desc.Node.internalFolder + "/normalMaps.sfm",
            group="",  # remove from command line
        ),
        desc.File(
            name="outputSfmDataNormalPNG",
            label="SfMData Normal PNG",
            description="Output SfMData file containing the normal maps information.",
            value=desc.Node.internalFolder + "/normalMapsPNG.sfm",
            group="", # remove from command line
        ),
        # these attributes are only here to describe more accurately the output of the node
        # by specifying that it generates 2 sequences of images
        # (see in Viewer2D.qml how these attributes can be used)
        desc.File(
            name="normals",
            label="Normal Maps Camera",
            description="Generated normal maps in the camera coordinate system.",
            semantic="image",
            value=desc.Node.internalFolder + "<POSE_ID>_normals.exr",
            group="",  # do not export on the command line
        ),
        desc.File(
            name="normalsPNG",
            label="Normal Maps Camera (in false colors)",
            description="Generated normal maps in the camera coordinate system (in false colors).",
            semantic="image",
            value=desc.Node.internalFolder + "<POSE_ID>_normals.png",
            group="", # do not export on the command line
        ),
        desc.File(
            name="normalsWorld",
            label="Normal Maps World",
            description="Generated normal maps in the world coordinate system.",
            semantic="image",
            value=desc.Node.internalFolder + "<POSE_ID>_normals_w.exr",
            group="",  # do not export on the command line
        ),

        desc.File(
            name="albedo",
            label="Albedo Maps",
            description="Generated albedo maps.",
            semantic="image",
            value=desc.Node.internalFolder + "<POSE_ID>_albedo.png",
            group="",  # do not export on the command line
        ),
    ]
