import bpy
import os
import mathutils
import math
import sys
import argparse
import json
import glob


def createParser():
    '''Create command line interface.'''
    # When --help or no args are given, print this help
    usage_text = (
        "Run blender in background mode with this script:"
        "  blender --background --python " + __file__ + " -- [options]"
    )

    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument(
        "--cameras", metavar='FILE', required=True,
        help="sfmData with the animated camera.",
    )
    parser.add_argument(
        "--useBackground", type=lambda x: (str(x).lower() == 'true'), required=True,
        help="Display the background image or not.",
    )
    parser.add_argument(
        "--undistortedImages", metavar='FILE', required=False,
        help="Save the generated file to the specified path",
    )
    parser.add_argument(
        "--model", metavar='FILE', required=True,
        help="Point Cloud or Mesh used in the rendering.",
    )
    parser.add_argument(
        "--particleSize", type=float, required=False,
        help="Scale of particles used to show the point cloud",
    )
    parser.add_argument(
        "--particleColor", type=str, required=False,
        help="Color of particles used to show the point cloud (SFM Data is .abc)",
    )
    parser.add_argument(
        "--edgeColor", type=str, required=False,
        help="Color of the edges of the rendered object (SFM Data is .obj)",
    )
    parser.add_argument(
        "--shading", type=str, required=False,
        help="Shading method for rendering the mesh",
    )
    parser.add_argument(
        "--output", metavar='FILE', required=True,
        help="Render an image to the specified path",
    )

    return parser


def parseSfMCameraFile(filepath):
    '''Retrieve cameras from SfM file in json format.'''
    with open(os.path.abspath(filepath), 'r') as file:
        sfm = json.load(file)
    views = sfm['views']
    intrinsics = sfm['intrinsics']
    poses = sfm['poses']
    return views, intrinsics, poses


def getFromId(data, key, identifier):
    '''Utility function to retrieve view, intrinsic or pose using their IDs.'''
    for item in data:
        if item[key] == identifier:
            return item
    return None


def setupCamera(intrinsic, pose):
    '''Setup Blender camera to match the given SfM camera.'''
    camObj = bpy.data.objects['Camera']
    camData = bpy.data.cameras['Camera']

    bpy.context.scene.render.resolution_x = int(intrinsic['width'])
    bpy.context.scene.render.resolution_y = int(intrinsic['height'])

    camData.sensor_width = float(intrinsic['sensorWidth'])
    camData.lens = float(intrinsic['focalLength'])

    tr = pose['pose']['transform']
    matPose = mathutils.Matrix.Identity(4)
    matPose[0][0] = float(tr['rotation'][0])
    matPose[0][1] = float(tr['rotation'][1])
    matPose[0][2] = float(tr['rotation'][2])
    matPose[1][0] = float(tr['rotation'][3])
    matPose[1][1] = float(tr['rotation'][4])
    matPose[1][2] = float(tr['rotation'][5])
    matPose[2][0] = float(tr['rotation'][6])
    matPose[2][1] = float(tr['rotation'][7])
    matPose[2][2] = float(tr['rotation'][8])
    matPose[0][3] = float(tr['center'][0])
    matPose[1][3] = float(tr['center'][1])
    matPose[2][3] = float(tr['center'][2])

    matConvert = mathutils.Matrix.Identity(4)
    matConvert[1][1] = -1
    matConvert[2][2] = -1

    camObj.matrix_world = matConvert @ matPose @ matConvert


def initScene():
    '''Initialize Blender scene.'''
    # Clear current scene (keep default camera)
    bpy.data.objects.remove(bpy.data.objects['Cube'])
    bpy.data.objects.remove(bpy.data.objects['Light'])
    # Set output format
    bpy.context.scene.render.image_settings.file_format = 'JPEG'


def initCompositing():
    '''Initialize Blender compositing graph for adding background image to render.'''
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.use_nodes = True
    bpy.context.scene.node_tree.nodes.new(type="CompositorNodeAlphaOver")
    bpy.context.scene.node_tree.nodes.new(type="CompositorNodeImage")
    bpy.context.scene.node_tree.links.new(
        bpy.context.scene.node_tree.nodes['Alpha Over'].outputs['Image'],
        bpy.context.scene.node_tree.nodes['Composite'].inputs['Image'])
    bpy.context.scene.node_tree.links.new(
        bpy.context.scene.node_tree.nodes['Image'].outputs['Image'],
        bpy.context.scene.node_tree.nodes['Alpha Over'].inputs[1])
    bpy.context.scene.node_tree.links.new(
        bpy.context.scene.node_tree.nodes['Render Layers'].outputs['Image'],
        bpy.context.scene.node_tree.nodes['Alpha Over'].inputs[2])


def setupRender(view, intrinsic, pose, outputDir):
    '''Setup rendering in Blender for a given view.'''
    setupCamera(intrinsic, pose)
    bpy.context.scene.render.filepath = os.path.abspath(outputDir + '/' + view['viewId'] + '.jpg')


def setupBackground(view, folderUndistorted):
    '''Retrieve undistorted image corresponding to view and use it as background.'''
    matches = glob.glob(folderUndistorted + '/*' + view['viewId'] + "*") # try with viewId
    if len(matches) == 0:
        baseImgName = os.path.splitext(os.path.basename(view['path']))[0]
        matches = glob.glob(folderUndistorted + '/*' + baseImgName + "*") # try with image name
    undistortedImgPath = matches[0]
    bpy.ops.image.open(filepath=undistortedImgPath)
    undistortedImgName = os.path.basename(undistortedImgPath)
    bpy.context.scene.node_tree.nodes["Image"].image = bpy.data.images[undistortedImgName]


def loadModel(filename):
    '''Load model in Alembic of OBJ format. Make sure orientation matches camera orientation.'''
    if filename.lower().endswith('.obj'):
        bpy.ops.import_scene.obj(filepath=filename, axis_forward='Y', axis_up='Z')
        meshName = os.path.splitext(os.path.basename(filename))[0]
        return bpy.data.objects[meshName], bpy.data.meshes[meshName]
    elif filename.lower().endswith('.abc'):
        bpy.ops.wm.alembic_import(filepath=filename)
        root = bpy.data.objects['mvgRoot']
        root.rotation_euler.rotate_axis('X', math.radians(-90.0))
        return bpy.data.objects['mvgPointCloud'], bpy.data.meshes['particleShape1']


def setupWireframeShading(mesh, color):
    '''Setup material for wireframe shading.'''
    # Initialize wireframe material
    material = bpy.data.materials.new('Wireframe')
    material.use_backface_culling = True
    material.use_nodes = True
    material.blend_method = 'BLEND'
    material.node_tree.links.clear()
    # Wireframe node
    nodeWireframe = material.node_tree.nodes.new(type='ShaderNodeWireframe')
    nodeWireframe.use_pixel_size = True
    nodeWireframe.inputs['Size'].default_value = 2.0
    # Emission node
    nodeEmission = material.node_tree.nodes.new(type='ShaderNodeEmission')
    nodeEmission.inputs['Color'].default_value = color
    # Transparent BSDF node
    nodeTransparent = material.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
    # Max Shader node
    nodeMix = material.node_tree.nodes.new(type='ShaderNodeMixShader')
    # Retrieve ouput node
    nodeOutput = material.node_tree.nodes['Material Output']
    # Connect nodes
    material.node_tree.links.new(nodeWireframe.outputs['Fac'], nodeMix.inputs['Fac'])
    material.node_tree.links.new(nodeTransparent.outputs['BSDF'], nodeMix.inputs[1])
    material.node_tree.links.new(nodeEmission.outputs['Emission'], nodeMix.inputs[2])
    material.node_tree.links.new(nodeMix.outputs['Shader'], nodeOutput.inputs['Surface'])
    # Apply material to mesh
    mesh.materials.clear()
    mesh.materials.append(material)


def setupLineArtShading(obj, mesh, color):
    '''Setup materials and Solidify modifier for line art shading.'''
    # Transparent filling material
    matFill = bpy.data.materials.new('Fill')
    matFill.use_backface_culling = True
    matFill.use_nodes = True
    matFill.blend_method = 'BLEND'
    matFill.show_transparent_back = False
    matFill.node_tree.links.clear()
    nodeTransparent = matFill.node_tree.nodes.new(type='ShaderNodeBsdfTransparent')
    nodeOutputFill = matFill.node_tree.nodes['Material Output']
    matFill.node_tree.links.new(nodeTransparent.outputs['BSDF'], nodeOutputFill.inputs['Surface'])
    # Colored edge material
    matEdge = bpy.data.materials.new('Edge')
    matEdge.use_backface_culling = True
    matEdge.use_nodes = True
    matEdge.blend_method = 'BLEND'
    matEdge.node_tree.links.clear()
    nodeEmission = matEdge.node_tree.nodes.new(type='ShaderNodeEmission')
    nodeEmission.inputs['Color'].default_value = color
    nodeOutputEdge = matEdge.node_tree.nodes['Material Output']
    matEdge.node_tree.links.new(nodeEmission.outputs['Emission'], nodeOutputEdge.inputs['Surface'])
    # Apply materials to mesh
    mesh.materials.clear()
    mesh.materials.append(matFill)
    mesh.materials.append(matEdge)
    # Solidify modifier
    solidify = obj.modifiers.new('Solidify', type='SOLIDIFY')
    solidify.thickness = -0.01
    solidify.use_rim = False
    solidify.use_flip_normals = True
    solidify.material_offset = 1


def setupPointCloudShading(obj, color, size):
    '''Setup material and geometry nodes for point cloud shading.'''
    # Colored filling material
    material = bpy.data.materials.new('PointCloud_Mat')
    material.use_nodes = True
    material.node_tree.links.clear()
    nodeEmission = material.node_tree.nodes.new(type='ShaderNodeEmission')
    nodeEmission.inputs['Color'].default_value = color
    nodeOutputFill = material.node_tree.nodes['Material Output']
    material.node_tree.links.new(nodeEmission.outputs['Emission'], nodeOutputFill.inputs['Surface'])
    # Geometry nodes modifier for particles
    geo = bpy.data.node_groups.new('Particles_Graph', type='GeometryNodeTree')
    mod = obj.modifiers.new('Particles_Modifier', type='NODES')
    mod.node_group = geo
    # Setup nodes
    nodeInput = geo.nodes.new(type='NodeGroupInput')
    nodeOutput = geo.nodes.new(type='NodeGroupOutput')
    nodeM2P = geo.nodes.new(type='GeometryNodeMeshToPoints')
    nodeIoP = geo.nodes.new(type='GeometryNodeInstanceOnPoints')
    nodeCube = geo.nodes.new(type='GeometryNodeMeshCube')
    nodeSize = geo.nodes.new(type='ShaderNodeValue')
    nodeSize.outputs['Value'].default_value = size
    nodeMat = geo.nodes.new(type='GeometryNodeSetMaterial')
    nodeMat.inputs[2].default_value = material
    # Connect nodes
    geo.links.new(nodeInput.outputs[0], nodeM2P.inputs['Mesh'])
    geo.links.new(nodeM2P.outputs['Points'], nodeIoP.inputs['Points'])
    geo.links.new(nodeCube.outputs['Mesh'], nodeIoP.inputs['Instance'])
    geo.links.new(nodeSize.outputs['Value'], nodeIoP.inputs['Scale'])
    geo.links.new(nodeIoP.outputs['Instances'], nodeMat.inputs['Geometry'])
    geo.links.new(nodeMat.outputs[0], nodeOutput.inputs[0])



def main():
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    parser = createParser()
    args = parser.parse_args(argv)

    if not argv:
        parser.print_help()
        return -1

    if args.useBackground and not args.undistortedImages:
        print("Error: --undistortedImages argument not given, aborting.")
        parser.print_help()
        return -1

    # Color palette (common for point cloud and mesh visualization)
    palette={
        'Grey':(0.2, 0.2, 0.2, 1),
        'White':(1, 1, 1, 1),
        'Red':(0.5, 0, 0, 1),
        'Green':(0, 0.5, 0, 1),
        'Magenta':(1.0, 0, 0.75, 1)
    }

    print("Init scene")
    initScene()

    print("Init compositing")
    if args.useBackground:
        initCompositing()

    print("Parse cameras SfM file")
    views, intrinsics, poses = parseSfMCameraFile(args.cameras)

    print("Load scene objects")
    sceneObj, sceneMesh = loadModel(args.model)

    print("Setup shading")
    if args.model.lower().endswith('.obj'):
        color = palette[args.edgeColor]
        if args.shading == 'wireframe':
            setupWireframeShading(sceneMesh, color)
        elif args.shading == 'line_art':
            setupLineArtShading(sceneObj, sceneMesh, color)
    elif args.model.lower().endswith('.abc'):
        color = palette[args.particleColor]
        setupPointCloudShading(sceneObj, color, args.particleSize)

    print("Render viewpoints")
    for view in views:
        intrinsic = getFromId(intrinsics, 'intrinsicId', view['intrinsicId'])
        if not intrinsic:
            continue

        pose = getFromId(poses, 'poseId', view['poseId'])
        if not pose:
            continue

        print("Rendering view " + view['viewId'])
        if args.useBackground:
            setupBackground(view, args.undistortedImages)
        setupRender(view, intrinsic, pose, args.output)
        bpy.ops.render.render(write_still=True)

    print("Done")
    return 0


if __name__ == "__main__":

    err = 1
    try:
        err = main()
    except Exception as e:
        print("\n" + str(e))
        sys.exit(err)
    sys.exit(err)

