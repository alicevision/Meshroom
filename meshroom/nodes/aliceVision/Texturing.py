__version__ = "6.0"

from meshroom.core import desc, Version
from meshroom.core.utils import COLORSPACES, VERBOSE_LEVEL

import logging


class Texturing(desc.AVCommandLineNode):
    commandLine = 'aliceVision_texturing {allParams}'
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Dense Reconstruction'
    documentation = '''
This node computes the texturing on the mesh.

If the mesh has no associated UV, it automatically computes UV maps.

For each triangle, it uses the visibility information associated to each vertex to retrieve the texture candidates.
It select the best cameras based on the resolution covering the triangle. Finally it averages the pixel values using multiple bands in the frequency domain.
Many cameras are contributing to the low frequencies and only the best ones contributes to the high frequencies.

## Online
[https://alicevision.org/#photogrammetry/texturing](https://alicevision.org/#photogrammetry/texturing)
'''

    inputs = [
        desc.File(
            name="input",
            label="Dense SfMData",
            description="SfMData file.",
            value="",
        ), 
        desc.File(
            name="imagesFolder",
            label="Images Folder",
            description="Use images from a specific folder instead of those specified in the SfMData file.\n"
                        "Filename should be the image UID.",
            value="",
        ),
        desc.File(
            name="normalsFolder",
            label="Normals Folder",
            description="Use normal maps from a specific folder to texture the mesh.\nFilename should be : uid_normalMap.",
            value="",
        ),
        desc.File(
            name="inputMesh",
            label="Mesh",
            description="Optional input mesh to texture. By default, it will texture the result of the reconstruction.",
            value="",
        ),
        desc.File(
            name="inputRefMesh",
            label="Ref Mesh",
            description="Optional input mesh to compute height maps and normal maps.\n"
                        "If not provided, no additional map with geometric information will be generated.",
            value="",
        ),
        desc.ChoiceParam(
            name="textureSide",
            label="Texture Side",
            description="Output texture size.",
            value=8192,
            values=[1024, 2048, 4096, 8192, 16384],
        ),
        desc.ChoiceParam(
            name="downscale",
            label="Texture Downscale",
            description="Texture downscale factor.",
            value=2,
            values=[1, 2, 4, 8],
        ),
        desc.ChoiceParam(
            name="outputMeshFileType",
            label="Mesh File Type",
            description="File type for the mesh output.",
            value="obj",
            values=["obj", "gltf", "fbx", "stl"],
        ),
        desc.GroupAttribute(
            name="colorMapping",
            label="Color Mapping",
            description="Color map parameters.",
            enabled=lambda node: (node.imagesFolder.value != ''),
            group=None,
            groupDesc=[
                desc.BoolParam(
                    name="enable",
                    label="Enable",
                    description="Generate textures if set to true.",
                    value=True,
                    invalidate=False,
                    group=None,
                ),
                desc.ChoiceParam(
                    name="colorMappingFileType",
                    label="File Type",
                    description="Texture file type.",
                    value="exr",
                    values=["exr", "png", "tiff", "jpg"],
                    enabled=lambda node: node.colorMapping.enable.value,
                ),
            ],
        ),
        desc.GroupAttribute(
            name="bumpMapping",
            label="Bump Mapping",
            description="Bump mapping parameters.",
            enabled=lambda node: (node.inputRefMesh.value != ''),
            group=None,
            groupDesc=[
                desc.BoolParam(
                    name="enable",
                    label="Enable",
                    description="Generate normal / bump maps if set to true.",
                    value=True,
                    invalidate=False,
                    group=None,
                ),
                desc.ChoiceParam(
                    name="bumpType",
                    label="Bump Type",
                    description="Export normal map or height map.",
                    value="Normal",
                    values=["Height", "Normal"],
                    enabled=lambda node: node.bumpMapping.enable.value,
                ),
                desc.ChoiceParam(
                    name="normalFileType",
                    label="File Type",
                    description="File type for the normal map texture.",
                    value="exr",
                    values=["exr", "png", "tiff", "jpg"],
                    enabled=lambda node: node.bumpMapping.enable.value and node.bumpMapping.bumpType.value == "Normal",
                ),
                desc.ChoiceParam(
                    name="heightFileType",
                    label="File Type",
                    description="File type for the height map texture.",
                    value="exr",
                    values=["exr",],
                    enabled=lambda node: node.bumpMapping.enable.value and node.bumpMapping.bumpType.value == "Height",
                ),
            ],
        ),
        desc.GroupAttribute(
            name="displacementMapping",
            label="Displacement Mapping",
            description="Displacement mapping parameters.",
            enabled=lambda node: (node.inputRefMesh.value != ""),
            group=None,
            groupDesc=[
                desc.BoolParam(
                    name="enable",
                    label="Enable",
                    description="Generate height maps for displacement.",
                    value=True,
                    invalidate=False,
                    group=None,
                ),
                desc.ChoiceParam(
                    name="displacementMappingFileType",
                    label="File Type",
                    description="File type for the height map texture.",
                    value="exr",
                    values=["exr"],
                    enabled=lambda node: node.displacementMapping.enable.value,
                ),
            ],
        ),
        desc.ChoiceParam(
            name="unwrapMethod",
            label="Unwrap Method",
            description="Method to unwrap input mesh if it does not have UV coordinates.\n"
                        " - Basic (> 600k faces) fast and simple. Can generate multiple atlases.\n"
                        " - LSCM (<= 600k faces): optimize space. Generates one atlas.\n"
                        " - ABF (<= 300k faces): optimize space and stretch. Generates one atlas.",
            value="Basic",
            values=["Basic", "LSCM", "ABF"],
        ),
        desc.BoolParam(
            name="useUDIM",
            label="Use UDIM",
            description="Use UDIM UV mapping.",
            value=True,
        ),
        desc.BoolParam(
            name="fillHoles",
            label="Fill Holes",
            description="Fill texture holes with plausible values.",
            value=False,
        ),
        desc.IntParam(
            name="padding",
            label="Padding",
            description="Texture edge padding size in pixels.",
            value=5,
            range=(0, 20, 1),
            advanced=True,
        ),
        desc.IntParam(
            name="multiBandDownscale",
            label="Multi Band Downscale",
            description="Width of frequency bands for multiband blending.",
            value=4,
            range=(0, 8, 2),
            advanced=True,
        ),
        desc.GroupAttribute(
            name="multiBandNbContrib",
            label="Multi-Band Contributions",
            groupDesc=[
                desc.IntParam(
                    name="high",
                    label="High Freq",
                    description="High frequency band.",
                    value=1,
                    range=None,
                ),
                desc.IntParam(
                    name="midHigh",
                    label="Mid-High Freq",
                    description="Mid-high frequency band.",
                    value=5,
                    range=None,
                ),
                desc.IntParam(
                    name="midLow",
                    label="Mid-Low Freq",
                    description="Mid-low frequency band.",
                    value=10,
                    range=None,
                ),
                desc.IntParam(
                    name="low",
                    label="Low Freq",
                    description="Low frequency band",
                    value=0,
                    range=None,
                ),
            ],
            description="Number of contributions per frequency band for multi-band blending (each frequency band also contributes to lower bands).",
            advanced=True,
        ),
        desc.BoolParam(
            name="useScore",
            label="Use Score",
            description="Use triangles scores (ie. reprojection area) for multi-band blending.",
            value=True,
            advanced=True,
        ),
        desc.FloatParam(
            name="bestScoreThreshold",
            label="Best Score Threshold",
            description="Setting this parameter to 0.0 disables filtering based on threshold to relative best score.",
            value=0.1,
            range=(0.0, 1.0, 0.01),
            advanced=True,
        ),
        desc.FloatParam(
            name="angleHardThreshold",
            label="Angle Hard Threshold",
            description="Setting this parameter to 0.0 disables angle hard threshold filtering.",
            value=90.0,
            range=(0.0, 180.0, 0.01),
            advanced=True,
        ),
        desc.ChoiceParam(
            name="workingColorSpace",
            label="Working Color Space",
            description="Color space for the texturing internal computation (does not impact the output file color space).",
            values=COLORSPACES,
            value="sRGB",
            advanced=True,
        ),
        desc.ChoiceParam(
            name="outputColorSpace",
            label="Output Color Space",
            description="Color space for the output texture files.",
            values=COLORSPACES,
            value="AUTO",
        ),
        desc.BoolParam(
            name="correctEV",
            label="Correct Exposure",
            description="Uniformize images exposure values.",
            value=True,
        ),
        desc.BoolParam(
            name="forceVisibleByAllVertices",
            label="Force Visible By All Vertices",
            description="Triangle visibility is based on the union of vertices visibility.",
            value=False,
            advanced=True,
        ),
        desc.BoolParam(
            name="flipNormals",
            label="Flip Normals",
            description="Option to flip face normals.\n"
                        "It can be needed as it depends on the vertices order in triangles and the convention changes from one software to another.",
            value=False,
            advanced=True,
        ),
        desc.ChoiceParam(
            name="visibilityRemappingMethod",
            label="Visibility Remapping Method",
            description="Method to remap visibilities from the reconstruction to the input mesh (Pull, Push, PullPush, MeshItself).",
            value="PullPush",
            values=["Pull", "Push", "PullPush", "MeshItself"],
            advanced=True,
        ),
        desc.FloatParam(
            name="subdivisionTargetRatio",
            label="Subdivision Target Ratio",
            description="Percentage of the density of the reconstruction as the target for the subdivision:\n"
                        " - 0: disable subdivision.\n"
                        " - 0.5: half density of the reconstruction.\n"
                        " - 1: full density of the reconstruction).",
            value=0.8,
            range=(0.0, 1.0, 0.001),
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
            name="output",
            label="Folder",
            description="Folder for output mesh: OBJ, material and texture files.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="outputMesh",
            label="Mesh",
            description="Output mesh file.",
            value=desc.Node.internalFolder + "texturedMesh.{outputMeshFileTypeValue}",
            group="",
            ),
        desc.File(
            name="outputMaterial",
            enabled=lambda node: node.outputMeshFileType.value == "obj",
            label="Material",
            description="Output material file.",
            value=desc.Node.internalFolder + "texturedMesh.mtl",
            group="",
            ),
        desc.File(
            name="outputTextures",
            label="Textures",
            description="Output texture files.",
            value=lambda attr: desc.Node.internalFolder + "texture_*." + attr.node.colorMapping.colorMappingFileType.value if attr.node.colorMapping.enable.value else "",
            group="",
        ),
    ]

    def upgradeAttributeValues(self, attrValues, fromVersion):
        if fromVersion < Version(6, 0):
            outputTextureFileType = attrValues['outputTextureFileType']
            if isinstance(outputTextureFileType, str):
                attrValues['colorMapping'] = {}
                attrValues['colorMapping']['colorMappingFileType'] = outputTextureFileType
        return attrValues
