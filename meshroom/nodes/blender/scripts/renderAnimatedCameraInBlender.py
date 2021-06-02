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
        "--sfMCameraPath", dest="SFM_cam_path", metavar='FILE', required=True,
        help="This text will be used to render an image",
    )

    parser.add_argument(
        "--useBackground", dest="Use_Background", type=strtobool, required=True,
        help="Diplay the background image or not.",
    )

    parser.add_argument(
        "--undistortedImages", dest="undisto_images", metavar='FILE', required=False,
        help="Save the generated file to the specified path",
    )

    parser.add_argument(
        "--sfMData", dest="SFM_Data", metavar='FILE', required=True,
        help="These info carry the Point Cloud or mesh we need.",
    )

    #Point Cloud Arguments (When SFM Data is .abc)

    parser.add_argument(
        "--pointCloudDensity", dest="Point_Cloud_Density", type=float, required=False,
        help="Number of point from the cloud rendered",
    )

    parser.add_argument(
        "--particleSize", dest="Particle_Size", type=float, required=False,
        help="Scale of every particle used to show the point cloud",
    )

    parser.add_argument(
        "--particleColor", dest="Particle_Color", type=str, required=False,
        help="Color of every particle used to show the point cloud (SFM Data is .abc)",
    )

    #Mesh Arguments (When SFM Data is .obj)

    parser.add_argument(
        "--edgeColor", dest="Edge_Color", type=str, required=False,
        help="Color of the edges of the rendered object (SFM Data is .obj)",
    )


    #Output Arguments

    parser.add_argument(
        "--outputFormat", dest="Output_Format", type=str, required=True,
        help="Format of the video output",
    )

    parser.add_argument(
        "--outputPath", dest="output_path", metavar='FILE', required=True,
        help="Render an image to the specified path",
    )


    args = parser.parse_args(argv)

    if not argv:
        parser.print_help()
        return

    if not args.undisto_images and args.Use_Background :
        print("Error: --undisto_images argument not given, aborting.")
        parser.print_help()
        return
        
    if not args.Point_Cloud_Density and args.SFM_Data.endswith('.abc'):
        print("Error: --Point_Cloud_Density argument not given, aborting.")
        parser.print_help()
        return

    if not args.Particle_Size and args.SFM_Data.endswith('.abc'):
        print("Error: --Particle_Size argument not given, aborting.")
        parser.print_help()
        return

    if not args.Particle_Color and args.SFM_Data.endswith('.abc'):
        print("Error: --Particle_Color argument not given, aborting.")
        parser.print_help()
        return

    if not args.Edge_Color and args.SFM_Data.endswith('.obj'):
        print("Error: --Edge_Color argument not given, aborting.")
        parser.print_help()
        return

    #Clear Current Scene
    try:
        for objects in bpy.data.objects:
            bpy.data.objects.remove(objects)
    except RuntimeError:
        print("Error: While clearing current scene")

    #The Switcher is the setting for most of the colors (if you want to add some, do it here and in the arguments of the node)
    # Keep in mind that we use the same switcher for both the Edge Color and the Particle Color settings.
    # So if you add a color to one of them in the node, might has well add it to the other.

    switcher={
        'Grey':(0.2, 0.2, 0.2, 1),
        'White':(1, 1, 1, 1),
        'Red':(0.5, 0, 0, 1),
        'Green':(0, 0.5, 0, 1),
        'Magenta':(1.0, 0, 0.75, 1)
    }

    # import Undistorted Images

    undis_imgs = []
    #Some of these variable will be very useful in the next steps keep them in mind
    number_of_frame = 0
    offset = 0
    first_image_name = ""
    try:
        # In this part of the code we take the undistorted images and we process some info about them
        # undis_imgs is the list of the images' names
        # first_image_name says it all in the name
        # The offset is important, it corresponds to the last part of the name of the first frame
        # In most case it will hopefully be 0 but the sequence may start from a more advanced frame
        if args.Use_Background :
            files = os.listdir(args.undisto_images)
            for f in files :
                if f.endswith(".exr") and not f.__contains__("UVMap"):
                    undis_imgs.append({"name":f})
            number_of_frame = len(undis_imgs)
            first_image_name = undis_imgs[0]['name']
            offset = int(re.findall(r'\d+', first_image_name)[-1]) - 1

    except RuntimeError:
        print("Error: while importing the undistorted images.")

    #import abc (Animated Camera)

    try:

        # In this part of the code we import the alembic in the cam_path to get the animated camera
        # We use cam_location and cam_obj to store information about this camera
        # We look for a camera (of type 'Persp') with the name 'anim' (not to confuse them with previously imported cams)

        # Once the cam has been found we select the main camera of the scene.
        # The rest of the code is setting up the display of the background image,
        # Since it's not a simple image but an image Sequence, we have to use the offset and the number of frame
        # Information taken from the previous block of code.
        # The frame method is the one that align with the Point Cloud althought this may change,
        # so feel free to try out the two other settings if something changes on previous nodes.
        # We also have to make the scene render film transparent because we want to be able to display
        # our background afterward in the next block of code

        bpy.ops.wm.alembic_import(filepath=args.SFM_cam_path)
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
                if args.Use_Background :
                    bpy.ops.image.open(filepath=args.undisto_images + "/" + first_image_name, directory=args.undisto_images, files=undis_imgs, relative_path=True, show_multiview=False)
                    bpy.data.cameras[obj.data.name].background_images.new()
                    bpy.data.cameras[obj.data.name].show_background_images = True
                    bpy.data.cameras[obj.data.name].background_images[0].image = bpy.data.images[first_image_name]
                    bpy.data.cameras[obj.data.name].background_images[0].frame_method = 'CROP'
                    bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_offset = offset
                    bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_duration = number_of_frame
                    bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_start = 1
                    bpy.context.scene.render.film_transparent = True
    except RuntimeError:
        print("Error: while importing the alembic file (Animated Camera).")

    #Place the particle plane
    try:

        # This is a key step if you are displaying a Point Cloud.
        # We are using a particle system later in the code to display the Point Cloud.
        # To make it so, we need a model for the particle, a object that will be repeated a lot to make a shape.
        # In order to do that we need a plane (one face only for optimisation purpose) that always face the camera.
        # So we made a plane and made it a child (in the parenting system) of the camera. That way whenever the cam
        # moves, the plane moves and turn accordingly.

        # Bmesh creates the plane and put it into the mesh. We change the size of the plane according to
        # the scale given in arguments. We need to adjust the plane's location because putting it at the
        # exact location of the camera blocks the view. Then, the switcher gives a RGBA color according to
        # the given argument. We have to use a material that uses 'Emission'
        # otherwise the particle is going to react to lights and we don't really need that (the color wouldn't be clear).
        # To do that we have to use the shader 'node_tree' we clear all links between nodes, create the emission node
        # and connect it to the 'Material Output' node (which is what we will see in render).
        # Finally we use the switcher to color the model.

        plane = bpy.data.meshes.new('Plane')
        objectsPlane = bpy.data.objects.new(name="Plane", object_data=plane)
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments = 1, y_segments = 1, size = 1.0)
        bm.to_mesh(plane)
        bm.free()
        if (args.SFM_Data.endswith('.abc')):
            objectsPlane.scale = mathutils.Vector((args.Particle_Size, args.Particle_Size, args.Particle_Size))
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
        if (args.SFM_Data.endswith('.abc')):
            objectsPlane.active_material.node_tree.nodes['Emission'].inputs[0].default_value = switcher.get(args.Particle_Color, 'Invalid Color')
        
    except RuntimeError:
        print("Error: while setting up the particle model.")

    if (args.SFM_Data.endswith('.abc')):
        # This part is all about importing the Point Cloud and setting up the Particle System.
        # After importing the alembic, we look for a specific mesh in the file. Again the hardcoded name would be a
        # problem if the previous nodes hadn't name it specificaly that (.001 because a mesh with the same name has
        # been imported with the animated camera).

        # Once the Point Cloud has been found. We make it the active object (important for the node_tree later).
        # Then, we create a particle system on it. Render_type set to object and the said object is the plane,
        # thanks to that the particle format is set to repeat the plane. Emit_from 'vert' so the points of the
        # point cloud are the one rendering the particle.
        # The count is the number of particle repeated on the point cloud. We use the rate given as arguments
        # to give a number. Most of the following settings are just formalities but use_rotation and use_rotation_instance,
        # those two make sure to use the same rotaion than the model (which is needed to have the particle always facing the camera).

        #import abc (Point Cloud)
        try:
            bpy.ops.wm.alembic_import(filepath=args.SFM_Data)
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

                    if (args.SFM_Data.endswith('.abc')):
                        particle_system.count = int(args.Point_Cloud_Density * len(obj.data.vertices.values()))
                    particle_system.frame_end = 1.0
                    particle_system.use_emit_random = False
                    particle_system.particle_size = 0.02
                    particle_system.physics_type = 'NO'
                    particle_system.use_rotations = True
                    particle_system.use_rotation_instance = True
                    particle_system.rotation_mode = 'GLOB_X'

        except RuntimeError:
            print("Error: while importing the alembic file (Point Cloud).")
    #Or import obj directly

    # The import via obj needs a bit of work too. For showing an outline of the object, we need to add two materials to the mesh :
    # Center and Edge, we are using a method that consists in having a "bold" effect on the Edge Material so we can see it
    # around the Center material. We do that by using a Solidify Modifier on which we flip normals and reduce Thickness to bellow zero.
    # The more the thickness get bellow zero, the more the egde will be largely revealed.
    elif (args.SFM_Data.endswith('.obj')):
        bpy.ops.import_scene.obj(filepath=args.SFM_Data)

        center = bpy.data.materials.new('Center')
        center.use_nodes = True
        center.node_tree.links.clear()
        center.node_tree.nodes.new(type='ShaderNodeEmission')
        center.node_tree.links.new(center.node_tree.nodes['Emission'].outputs['Emission'], center.node_tree.nodes['Material Output'].inputs['Surface'])
        center.node_tree.nodes['Emission'].inputs[0].default_value = (0,0,0,0)

        if not args.Use_Background and args.SFM_Data.endswith('.obj'):
            center.node_tree.nodes['Emission'].inputs[0].default_value = (0.05, 0.05, 0.05, 1) #Same Color as the no background color in blender

        
        edge = bpy.data.materials.new('Edge')

        edge.use_nodes = True
        edge.node_tree.links.clear()
        edge.node_tree.nodes.new(type='ShaderNodeEmission')
        edge.use_backface_culling = True
        edge.node_tree.links.new(edge.node_tree.nodes['Emission'].outputs['Emission'], edge.node_tree.nodes['Material Output'].inputs['Surface'])
        edge.node_tree.nodes['Emission'].inputs[0].default_value = switcher.get(args.Edge_Color, 'Invalid Color')
        
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
        print("SFM_Data isn't in the right format,  alembics(.abc) and object(.obj) only are supported")

    #WE HAVE TO USE THE COMPOSITING GRAPH TO MAKE THE BACKGROUND IMAGE VISIBLE
    # We setup all the nodes in the first place, even if we don't need them in our configuration. We put the setting in all of them.
    # Only after having done that we can control which of the node we link in the graph according to the option we were given.
    # If the SFM Data is a Mesh, its extension is .obj so we have to build the graph accordingly. If the Background image setting was activated,
    # we need to include it in our node tree through the "Image" and Scale node.
    try:
        bpy.context.scene.use_nodes = True

        #CREATE ALL NODES WE NEED (regardless of the options)
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeAlphaOver")
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeScale")
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeImage")

        bpy.context.scene.node_tree.nodes.new(type="CompositorNodePremulKey")
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeMixRGB")

        #SET THEM UP CORRECTLY (still regardless of the option)
        bpy.data.scenes["Scene"].node_tree.nodes["Mix"].blend_type = 'LIGHTEN'
        bpy.data.scenes["Scene"].node_tree.nodes["Image"].frame_duration = number_of_frame
        bpy.data.scenes["Scene"].node_tree.nodes["Image"].frame_offset = offset
        bpy.data.scenes["Scene"].node_tree.nodes["Scale"].space = 'RENDER_SIZE'
        bpy.data.scenes["Scene"].node_tree.nodes["Scale"].frame_method = 'CROP'

        #LINKS THE NODES THAT NEEDS TO BE LINKED
        if args.Use_Background :
            if args.SFM_Data.endswith('.obj'):
                bpy.context.scene.node_tree.nodes["Image"].image = bpy.data.images[first_image_name]
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Mix'].outputs['Image'], bpy.context.scene.node_tree.nodes['Composite'].inputs['Image'])
                #Two Inputs of AlphaOver are named "Image" so we'll use index instead
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Render Layers'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Convert'].inputs['Image'])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Alpha Convert'].outputs['Image'], bpy.context.scene.node_tree.nodes['Mix'].inputs[2])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Scale'].outputs['Image'], bpy.context.scene.node_tree.nodes['Mix'].inputs[1])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Image'].outputs['Image'], bpy.context.scene.node_tree.nodes['Scale'].inputs['Image'])
            else:
                bpy.context.scene.node_tree.nodes["Image"].image = bpy.data.images[first_image_name]
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Alpha Over'].outputs['Image'], bpy.context.scene.node_tree.nodes['Composite'].inputs['Image'])
                #Two Inputs of AlphaOver are named "Image" so we'll use index instead
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Render Layers'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Over'].inputs[2])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Scale'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Over'].inputs[1])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Image'].outputs['Image'], bpy.context.scene.node_tree.nodes['Scale'].inputs['Image'])
        else:
            if args.SFM_Data.endswith('.obj'):
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Mix'].outputs['Image'], bpy.context.scene.node_tree.nodes['Composite'].inputs['Image'])
                #Two Inputs of AlphaOver are named "Image" so we'll use index instead
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Render Layers'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Convert'].inputs['Image']) 
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Alpha Convert'].outputs['Image'], bpy.context.scene.node_tree.nodes['Mix'].inputs[2])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Scale'].outputs['Image'], bpy.context.scene.node_tree.nodes['Mix'].inputs[1])
                bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Image'].outputs['Image'], bpy.context.scene.node_tree.nodes['Scale'].inputs['Image'])
    except RuntimeError:
        print("Error: while composing the compositing graph.")

    ## Starts the rendering and launchs it with a blender animator player

    try:
        # Setup the render format and filepath
        bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
        if args.Output_Format == 'mkv':
            bpy.context.scene.render.ffmpeg.format = 'MKV'
        elif args.Output_Format == 'avi':
            bpy.context.scene.render.ffmpeg.format = 'AVI'
        elif args.Output_Format == 'mov':
            bpy.context.scene.render.ffmpeg.format = 'QUICKTIME'
        else:
            bpy.context.scene.render.ffmpeg.format = 'MPEG4'
        bpy.context.scene.render.filepath = args.output_path + '/render.' + args.Output_Format
        # Render everything on to the filepath
        bpy.ops.render.render(animation=True)
        # Starts a player automatically to play the output (Usefull for developpers to see what they do but it doesn't really have its place in a software)
        # bpy.ops.render.play_rendered_anim()
    except RuntimeError:
        print("Error: while rendering the scene.")
    


if __name__ == "__main__":
    main()