import bpy
import bmesh
import os
import re
import mathutils
import sys   # to get command line args
import argparse  # to parse options for us and print a nice help message
from distutils.util import strtobool


def main():
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = (
        "Run blender in background mode with this script:"
        "  blender --background --python " + __file__ + " -- [options]"
    )

    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument(
        "--sfmCameraPath", metavar='FILE', required=True,
        help="sfmData with the animated camera.",
    )

    parser.add_argument(
        "--useBackground", type=strtobool, required=True,
        help="Diplay the background image or not.",
    )

    parser.add_argument(
        "--undistortedImages", metavar='FILE', required=False,
        help="Save the generated file to the specified path",
    )

    parser.add_argument(
        "--model", metavar='FILE', required=True,
        help="Point Cloud or Mesh used in the rendering.",
    )

    # Point Cloud Arguments (when SFM Data is .abc)

    parser.add_argument(
        "--pointCloudDensity", type=float, required=False,
        help="Number of point from the cloud rendered",
    )

    parser.add_argument(
        "--particleSize", type=float, required=False,
        help="Scale of particles used to show the point cloud",
    )

    parser.add_argument(
        "--particleColor", type=str, required=False,
        help="Color of particles used to show the point cloud (SFM Data is .abc)",
    )

    # Mesh Arguments (when SFM Data is .obj)

    parser.add_argument(
        "--edgeColor", type=str, required=False,
        help="Color of the edges of the rendered object (SFM Data is .obj)",
    )

    # Output Arguments

    parser.add_argument(
        "--videoFormat", type=str, required=True,
        help="Format of the video output",
    )

    parser.add_argument(
        "--outputPath", metavar='FILE', required=True,
        help="Render an image to the specified path",
    )

    args = parser.parse_args(argv)

    if not argv:
        parser.print_help()
        return -1

    if not args.undistortedImages and args.useBackground:
        print("Error: --undistortedImages argument not given, aborting.")
        parser.print_help()
        return -1

    # Clear Current Scene
    try:
        for objects in bpy.data.objects:
            bpy.data.objects.remove(objects)
    except RuntimeError:
        print("Error while clearing current scene")
        raise

    # The Switcher is the setting for most of the colors (if you want to add some, do it here and in the arguments of the node)
    # Keep in mind that we use the same switcher for both the Edge Color and the Particle Color settings.
    # So if you add a color to one of them in the node, might has well add it to the other.

    switcher={
        'Grey':(0.2, 0.2, 0.2, 1),
        'White':(1, 1, 1, 1),
        'Red':(0.5, 0, 0, 1),
        'Green':(0, 0.5, 0, 1),
        'Magenta':(1.0, 0, 0.75, 1)
    }

    print("Import Undistorted Images")

    undis_imgs = []
    # Some of these variable will be very useful in the next steps keep them in mind
    number_of_frame = 0
    offset = 0
    first_image_name = ""
    try:
        # In this part of the code we take the undistorted images and we process some info about them
        # undis_imgs is the list of the images' names
        # first_image_name says it all in the name
        # The offset is important, it corresponds to the last part of the name of the first frame.
        # In most case, it will be 0 but the sequence may start from a more advanced frame.
        if args.useBackground:
            files = os.listdir(args.undistortedImages)
            for f in files :
                if f.endswith(".exr") and not f.__contains__("UVMap"):
                    undis_imgs.append({"name":f})
            number_of_frame = len(undis_imgs)
            print("undis_imgs: " + str(undis_imgs))
            first_image_name = undis_imgs[0]['name']
            offset = int(re.findall(r'\d+', first_image_name)[-1]) - 1

    except RuntimeError:
        print("Error while importing the undistorted images.")
        raise

    print("Import Animated Camera")

    try:

        # In this part of the code we import the alembic in the cam_path to get the animated camera
        # We use cam_location and cam_obj to store information about this camera
        # We look for a camera (of type 'Persp') with the name 'anim' (not to confuse them with previously imported cams)

        # Once the cam has been found we select the main camera of the scene.
        # The rest of the code is setting up the display of the background image,
        # As it is not a simple image but an image Sequence, we have to use the offset and the number of frames.

        # We also have to make the scene render film transparent because we want to be able to display
        # our background afterwards.

        bpy.ops.wm.alembic_import(filepath=args.sfmCameraPath)
        animated_cams = bpy.context.selected_editable_objects[:]
        cam_location = mathutils.Vector((0, 0, 0))
        cam_obj = None
        for obj in animated_cams:
            if obj.data and obj.data.type == 'PERSP' and "anim" in obj.data.name:
                bpy.context.scene.collection.objects.link(obj)
                bpy.context.view_layer.objects.active = obj
                bpy.context.scene.camera = obj
                cam_location = obj.location
                cam_obj = obj
                if args.useBackground :
                    bpy.ops.image.open(filepath=args.undistortedImages + "/" + first_image_name, directory=args.undistortedImages, files=undis_imgs, relative_path=True, show_multiview=False)
                    bpy.data.cameras[obj.data.name].background_images.new()
                    bpy.data.cameras[obj.data.name].show_background_images = True
                    bpy.data.cameras[obj.data.name].background_images[0].image = bpy.data.images[first_image_name]
                    bpy.data.cameras[obj.data.name].background_images[0].frame_method = 'CROP'
                    bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_offset = offset
                    bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_duration = number_of_frame
                    bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_start = 1
                    bpy.context.scene.render.film_transparent = True
    except RuntimeError:
        print("Error while importing the alembic file (Animated Camera): " + args.sfmCameraPath)
        raise

    print("Create the particle plane")

    try:

        # We are using a particle system later in the code to display the Point Cloud.
        # We need to setup a model for the particle, a plane that always face the camera.
        # It is declared as a child of the camera in the parenting system, so when the camera moves, the plane moves accordingly.

        # We use an 'Emission' material so it does not react to lights.
        # To do that we have to use the shader 'node_tree' we clear all links between nodes, create the emission node
        # and connect it to the 'Material Output' node.

        plane = bpy.data.meshes.new('Plane')
        objectsPlane = bpy.data.objects.new(name="Plane", object_data=plane)
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments = 1, y_segments = 1, size = 1.0)
        bm.to_mesh(plane)
        bm.free()
        if args.model.lower().endswith('.abc'):
            objectsPlane.scale = mathutils.Vector((args.particleSize, args.particleSize, args.particleSize))
        cam_location.y += -2.0
        objectsPlane.location = cam_location
        bpy.context.scene.collection.objects.link(objectsPlane)
        bpy.data.objects['Plane'].parent = cam_obj
        bpy.context.view_layer.objects.active = objectsPlane

        col = bpy.data.materials.new('Color')
        objectsPlane.active_material = col
        objectsPlane.active_material.use_nodes = True
        objectsPlane.active_material.node_tree.links.clear()
        objectsPlane.active_material.node_tree.nodes.new(type='ShaderNodeEmission')
        objectsPlane.active_material.node_tree.links.new(objectsPlane.active_material.node_tree.nodes['Emission'].outputs['Emission'], objectsPlane.active_material.node_tree.nodes['Material Output'].inputs['Surface'])
        if args.model.lower().endswith('.abc'):
            objectsPlane.active_material.node_tree.nodes['Emission'].inputs[0].default_value = switcher.get(args.particleColor, 'Invalid Color')
        
    except RuntimeError:
        print("Error: while setting up the particle model.")
        raise


    if args.model.lower().endswith('.abc'):

        print("Import ABC Point Cloud")

        # After importing the alembic, we look for a specific Point Cloud in the file.
        # We make it the active object (important for the node_tree later).
        # Then, we create a particle system on it. Render_type set to object and the said object is the plane.
        # Emit_from 'vert' so the points of the point cloud are the one rendering the particle.
        # The count is the number of particles repeated on the point cloud. We use the rate given as arguments
        # to give a number.
        # use_rotation and use_rotation_instance ensure that we use the same rotation than the model (which is needed to have the particle always facing the camera).

        # Import Point Cloud
        try:
            bpy.ops.wm.alembic_import(filepath=args.model)
            all_abc_info = bpy.context.selected_editable_objects[:]
            for obj in all_abc_info:
                if obj.name == 'mvgPointCloud.001': #May have a problem with such hard code
                    bpy.context.scene.collection.objects.link(obj)
                    bpy.context.view_layer.objects.active = obj
                    obj.modifiers.new("ParticleSystem", "PARTICLE_SYSTEM")
                    particle_system = bpy.data.particles["ParticleSystem"]
                    particle_system.render_type = 'OBJECT'

                    particle_system.instance_object = bpy.data.objects["Plane"]
                    particle_system.emit_from = 'VERT'

                    if args.model.lower().endswith('.abc'):
                        particle_system.count = int(args.pointCloudDensity * len(obj.data.vertices.values()))
                    particle_system.frame_end = 1.0
                    particle_system.use_emit_random = False
                    particle_system.particle_size = 0.02
                    particle_system.physics_type = 'NO'
                    particle_system.use_rotations = True
                    particle_system.use_rotation_instance = True
                    particle_system.rotation_mode = 'GLOB_X'

        except RuntimeError:
            print("Error while importing the alembic file (Point Cloud): " + args.model)
            raise


    # For showing an outline of the object, we need to add two materials to the mesh:
    # Center and Edge, we are using a method that consists in having a "bold" effect on the Edge Material so we can see it
    # around the Center material. We use a Solidify Modifier on which we flip normals and reduce Thickness to bellow zero.
    # The more the thickness get bellow zero, the more the egde will be largely revealed.
    elif args.model.lower().endswith('.obj'):
        print("Import OBJ")

        bpy.ops.import_scene.obj(filepath=args.model)

        center = bpy.data.materials.new('Center')
        center.use_nodes = True
        center.node_tree.links.clear()
        center.node_tree.nodes.new(type='ShaderNodeEmission')
        center.node_tree.links.new(center.node_tree.nodes['Emission'].outputs['Emission'], center.node_tree.nodes['Material Output'].inputs['Surface'])
        center.node_tree.nodes['Emission'].inputs[0].default_value = (0,0,0,0)

        if not args.useBackground and args.model.lower().endswith('.obj'):
            center.node_tree.nodes['Emission'].inputs[0].default_value = (0.05, 0.05, 0.05, 1) #Same Color as the no background color in blender

        edge = bpy.data.materials.new('Edge')

        edge.use_nodes = True
        edge.node_tree.links.clear()
        edge.node_tree.nodes.new(type='ShaderNodeEmission')
        edge.use_backface_culling = True
        edge.node_tree.links.new(edge.node_tree.nodes['Emission'].outputs['Emission'], edge.node_tree.nodes['Material Output'].inputs['Surface'])
        edge.node_tree.nodes['Emission'].inputs[0].default_value = switcher.get(args.edgeColor, 'Invalid Color')

        bpy.data.meshes['mesh'].materials.clear()
        bpy.data.meshes['mesh'].materials.append(bpy.data.materials['Center'])
        bpy.data.meshes['mesh'].materials.append(bpy.data.materials['Edge'])

        print(bpy.data.meshes['mesh'].materials.values())

        bpy.data.objects['mesh'].modifiers.new('New', type='SOLIDIFY')
        bpy.data.objects['mesh'].modifiers["New"].thickness = -0.01
        bpy.data.objects['mesh'].modifiers["New"].use_rim = False
        bpy.data.objects['mesh'].modifiers["New"].use_flip_normals = True
        bpy.data.objects['mesh'].modifiers["New"].material_offset = 1
    else:
        raise ValueError("sfmData: unknown file format, only alembic (.abc) and object (.obj) are supported: " + args.model)

    print("Create compositing graph")

    # We use the compositing graph to add the background image.
    # If the SFM Data is a Mesh, its extension is .obj so we have to build the graph accordingly. If the Background image setting was activated,
    # we need to include it in our node tree through the "Image" and Scale node.
    try:
        bpy.context.scene.use_nodes = True

        # Create all the nodes that we could need
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeAlphaOver")
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeScale")
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeImage")

        bpy.context.scene.node_tree.nodes.new(type="CompositorNodePremulKey")
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeMixRGB")

        bpy.data.scenes["Scene"].node_tree.nodes["Mix"].blend_type = 'LIGHTEN'
        bpy.data.scenes["Scene"].node_tree.nodes["Image"].frame_duration = number_of_frame
        bpy.data.scenes["Scene"].node_tree.nodes["Image"].frame_offset = offset
        bpy.data.scenes["Scene"].node_tree.nodes["Scale"].space = 'RENDER_SIZE'
        bpy.data.scenes["Scene"].node_tree.nodes["Scale"].frame_method = 'CROP'

        # create links between nodes
        if args.useBackground :
            if args.model.lower().endswith('.obj'):
                bpy.context.scene.node_tree.nodes["Image"].image = bpy.data.images[first_image_name]
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Mix'].outputs['Image'], bpy.context.scene.node_tree.nodes['Composite'].inputs['Image'])
                # Two Inputs of AlphaOver are named "Image" so we use indexes instead
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Render Layers'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Convert'].inputs['Image'])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Alpha Convert'].outputs['Image'], bpy.context.scene.node_tree.nodes['Mix'].inputs[2])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Scale'].outputs['Image'], bpy.context.scene.node_tree.nodes['Mix'].inputs[1])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Image'].outputs['Image'], bpy.context.scene.node_tree.nodes['Scale'].inputs['Image'])
            else:
                bpy.context.scene.node_tree.nodes["Image"].image = bpy.data.images[first_image_name]
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Alpha Over'].outputs['Image'], bpy.context.scene.node_tree.nodes['Composite'].inputs['Image'])
                # Two Inputs of AlphaOver are named "Image" so we use indexes instead
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Render Layers'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Over'].inputs[2])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Scale'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Over'].inputs[1])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Image'].outputs['Image'], bpy.context.scene.node_tree.nodes['Scale'].inputs['Image'])
        else:
            if args.model.lower().endswith('.obj'):
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Mix'].outputs['Image'], bpy.context.scene.node_tree.nodes['Composite'].inputs['Image'])
                # Two Inputs of AlphaOver are named "Image" so we use indexes instead
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Render Layers'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Convert'].inputs['Image']) 
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Alpha Convert'].outputs['Image'], bpy.context.scene.node_tree.nodes['Mix'].inputs[2])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Scale'].outputs['Image'], bpy.context.scene.node_tree.nodes['Mix'].inputs[1])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Image'].outputs['Image'], bpy.context.scene.node_tree.nodes['Scale'].inputs['Image'])
    except RuntimeError:
        print("Error while creating the compositing graph.")
        raise

    try:
        # Setup the render format and filepath
        bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
        if args.videoFormat == 'mkv':
            bpy.context.scene.render.ffmpeg.format = 'MKV'
        elif args.videoFormat == 'avi':
            bpy.context.scene.render.ffmpeg.format = 'AVI'
        elif args.videoFormat == 'mov':
            bpy.context.scene.render.ffmpeg.format = 'QUICKTIME'
        else:
            bpy.context.scene.render.ffmpeg.format = 'MPEG4'
        bpy.context.scene.render.filepath = args.outputPath + '/render.' + args.videoFormat

        print("Start Rendering")
        # Render everything on to the filepath
        bpy.ops.render.render(animation=True)
        print("Rendering Done")
        # Starts a player automatically to play the output
        # bpy.ops.render.play_rendered_anim()
    except RuntimeError:
        print("Error while rendering the scene")
        raise

    return 0


if __name__ == "__main__":

    err = 1
    try:
        err = main()
    except Exception as e:
        print("\n" + str(e))
        sys.exit(err)
    sys.exit(err)

