import bpy
import bmesh
import os
import re
import mathutils
import math
import sys   # to get command line args
import argparse  # to parse options for us and print a nice help message
from math import radians

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
        "--sfMData", dest="SFM_Data", metavar='FILE', required=True,
        help="These info carry the cloud point we need.",
    )

    parser.add_argument(
        "--sfMCameraPath", dest="SFM_cam_path", metavar='FILE', required=True,
        help="This text will be used to render an image",
    )

    parser.add_argument(
        "--cloudPointDensity", dest="Cloud_Point_Density", type=float, required=True,
        help="Number of point from the cloud rendered",
    )

    parser.add_argument(
        "--particleSize", dest="Particle_Size", type=float, required=True,
        help="Scale of every particle used to show the cloud of point",
    )

    parser.add_argument(
        "--undistortedImages", dest="undisto_images", metavar='FILE', required=True,
        help="Save the generated file to the specified path",
    )

    parser.add_argument(
        "--outputPath", dest="output_path", metavar='FILE', required=True,
        help="Render an image to the specified path",
    )

    parser.add_argument(
        "--particleColor", dest="Particle_Color", metavar=str, required=True,
        help="Color of every particle used to show the cloud of point",
    )

    args = parser.parse_args(argv)

    if not argv:
        parser.print_help()
        return

    if not args.SFM_cam_path:
        print("Error: --SFM_cam_path argument not given, aborting.")
        parser.print_help()
        return

    if not args.undisto_images:
        print("Error: --undisto_images argument not given, aborting.")
        parser.print_help()
        return
        
    if not args.Cloud_Point_Density:
        print("Error: --Cloud_Point_Density argument not given, aborting.")
        parser.print_help()
        return

    if not args.Particle_Size:
        print("Error: --Particle_Size argument not given, aborting.")
        parser.print_help()
        return

    if not args.output_path:
        print("Error: --output_path argument not given, aborting.")
        parser.print_help()
        return

    if not args.Particle_Color:
        print("Error: --Particle_Color argument not given, aborting.")
        parser.print_help()
        return

    #Clear Current Scene
    try:
        for objects in bpy.data.objects:
            bpy.data.objects.remove(objects)
    except:
        print("Error: While clearing current scene")

    # import Undistorted Images

    undis_imgs = []
    #Some of these info will be very useful in the next steps keep them in mind
    number_of_frame = 0
    offset = 0
    first_image_name = ""
    try:
        # In this part of the code we take the undistorted images and we process some info about them
        # undis_imgs is the list of the images' names
        # first_image_name says it all in the name
        # The offset is important, it corresponds to the last part of the name of the first frame
        # In most case it will hopefully be 0 but the sequence may start from another frame

        files = os.listdir(args.undisto_images)
        for f in files :
            if f.endswith(".exr") and not f.__contains__("UVMap"):
                undis_imgs.append({"name":f})
        number_of_frame = len(undis_imgs)
        first_image_name = undis_imgs[0]['name']
        offset = int(re.findall(r'\d+', first_image_name)[-1]) - 1

    except:
        print("Error: while importing the undistorted images.")

    #import abc (Animated Camera)

    try:

        # In this part of the code we import the alembic in the cam_path to get the animated camera
        # We use cam_location and cam_obj to store information about this camera
        # We look for a camera (of type 'Persp') with the name 'anim' (not to confuse them with previously imported cams)
        # Such hard code is not a problem in this case because all imported cams come from previous nodes and are named specificaly

        # Once the cam has been found we select is make it the main camera of the scene
        # The rest of the code is setting up the display of the background image,
        # Since it's not a simple image but an image Sequence, we have to use the offset and the number of frame
        # Information taken from the previous block of code.
        # The frame method is the one that align with the Cloud of Point althought this may change
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
                bpy.ops.image.open(filepath=args.undisto_images + "/" + first_image_name, directory=args.undisto_images, files=undis_imgs, relative_path=True, show_multiview=False)
                bpy.data.cameras[obj.data.name].background_images.new()
                bpy.data.cameras[obj.data.name].show_background_images = True 
                bpy.data.cameras[obj.data.name].background_images[0].image = bpy.data.images[first_image_name]
                bpy.data.cameras[obj.data.name].background_images[0].frame_method = 'CROP'
                bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_offset = offset
                bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_duration = number_of_frame
                bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_start = 1
                bpy.context.scene.render.film_transparent = True
    except:
        print("Error: while importing the alembic file (Animated Camera).")

    #Place the particle plane
    try:

        # This is a key step if you are displaying a cloud point.
        # We are using a particle system later in the code to display the cloud point.
        # To make it so, we need a model for the particle, a object that will be repeated a lot to make a shape.
        # In order to do that we need a plane (one face only for optimisation purpose) that always face the camera.
        # So we made a plane and made it a child (in the parenting system) of the camera. That way whenever the cam
        # moves, the plane moves and turn accordingly.

        # Bmesh creates the plane and put it into the mesh. We change the size of the plane according to
        # the scale given in arguments. We need to adjust the plane's location because putting it at the 
        # exact location of the camera blocks the view. Then, the switcher give a RGBA color according to
        # the given argument... This is where it gets harder. We have to use a material that uses 'Emission'
        # otherwise the particle is going to react to lights and we don't really need that (the color wouldn't be clear).
        # To do that we have to use the shader 'node_tree' we clear all links between nodes, create the emission node
        # and connects it to the 'Material Output' node (which is what we will see in render). 
        # Finally we use the switcher to color the model. 

        plane = bpy.data.meshes.new('Plane')
        objectsPlane = bpy.data.objects.new(name="Plane", object_data=plane)
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments = 1, y_segments = 1, size = 1.0)
        bm.to_mesh(plane)
        bm.free()
        objectsPlane.scale = mathutils.Vector((args.Particle_Size, args.Particle_Size, args.Particle_Size))
        cam_location.y += -2.0
        objectsPlane.location = cam_location
        bpy.context.scene.collection.objects.link(objectsPlane)
        bpy.data.objects['Plane'].parent = cam_obj
        bpy.context.view_layer.objects.active = objectsPlane


        switcher={
            'Grey':(0.2, 0.2, 0.2, 1),
            'White':(1, 1, 1, 1),
            'Red':(0.5, 0, 0, 1),
            'Green':(0, 0.5, 0, 1),
            'Magenta':(1.0, 0, 0.75, 1)
        }

        col = bpy.data.materials.new('Color')
        objectsPlane.active_material = col
        objectsPlane.active_material.use_nodes = True
        objectsPlane.active_material.node_tree.links.clear()
        objectsPlane.active_material.node_tree.nodes.new(type='ShaderNodeEmission')
        objectsPlane.active_material.node_tree.links.new(objectsPlane.active_material.node_tree.nodes['Emission'].outputs['Emission'], objectsPlane.active_material.node_tree.nodes['Material Output'].inputs['Surface'])
        objectsPlane.active_material.node_tree.nodes['Emission'].inputs[0].default_value = switcher.get(args.Particle_Color, 'Invalid Color')
        
    except:
        print("Error: while setting up the particle model.")

    if (args.SFM_Data.endswith('.abc')):
        # This part is all about importing the Cloud Point and setting up the Particle System to make a good render
        # After importing the alembic we look for a specific meshe in the file. Again the hard coded name would be a
        # problem if the previous nodes hadn't name it specificaly that (.001 because a meshe with the same name has 
        # been imported with the animated camera).

        # Once the cloud point has been found. We make it the active object (important for the node_tree later). 
        # Then, we create a particle system on it. Render_type set to object and the said object is the plane, 
        # thanks to that the particle format is set to repeat the plane. Emit_from 'vert' so the points of the 
        # cloud of point are the one rendering the particle.
        # The count is the number of particle repeated on the cloud of point. We use the rate given as arguments
        # to give a number. Most of the following settings are just formalities except use_rotation and use_rotation_instance
        # those two make sure to use the same roation as the model which is vital to have the particle always facing the camera.

        #import abc (Cloud Point)
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

                    particle_system.count = int(args.Cloud_Point_Density * len(obj.data.vertices.values()))
                    particle_system.frame_end = 1.0
                    particle_system.use_emit_random = False
                    particle_system.particle_size = 0.02
                    particle_system.physics_type = 'NO'
                    particle_system.use_rotations = True
                    particle_system.use_rotation_instance = True
                    particle_system.rotation_mode = 'GLOB_X'

        except:
            print("Error: while importing the alembic file (Cloud Point).")
    #Or import obj directly
    elif (args.SFM_Data.endswith('.obj')):
        bpy.ops.import_scene.obj(filepath=args.SFM_Data)
    else:
        print("SFM_Data isn't in the right format,  alembics(.abc) and object(.obj) only are supported")



    #WE HAVE TO USE THE GRAPH TO MAKE THE BACKGROUND IMAGE VISIBLE
    try:
        bpy.context.scene.use_nodes = True 

        #CREATE ALL NODES WE NEED (Color.AlphaOver, Input.Image, Distort.Scale)
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeAlphaOver")
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeScale")
        bpy.context.scene.node_tree.nodes.new(type="CompositorNodeImage")

        #SET THEM UP CORRECTLY
        bpy.data.scenes["Scene"].node_tree.nodes["Image"].frame_duration = number_of_frame
        bpy.data.scenes["Scene"].node_tree.nodes["Image"].frame_offset = offset
        bpy.data.scenes["Scene"].node_tree.nodes["Scale"].space = 'RENDER_SIZE'
        bpy.data.scenes["Scene"].node_tree.nodes["Scale"].frame_method = 'CROP'
        bpy.context.scene.node_tree.nodes["Image"].image = bpy.data.images[first_image_name]

        #LINKS THE NODES THAT NEEDS TO BE LINKED
        bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Alpha Over'].outputs['Image'], bpy.context.scene.node_tree.nodes['Composite'].inputs['Image'])
        #Two Inputs of AlphaOver are named "Image" so we'll use index instead
        bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Render Layers'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Over'].inputs[2]) 
        bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Scale'].outputs['Image'], bpy.context.scene.node_tree.nodes['Alpha Over'].inputs[1])
        bpy.context.scene.node_tree.links.new(bpy.context.scene.node_tree.nodes['Image'].outputs['Image'], bpy.context.scene.node_tree.nodes['Scale'].inputs['Image'])
    except:
        print("Error: while composing the compositing graph.")

    ## Starts the rendering and launchs it with a blender animator player

    try:
        # Setup the render format and filepath
        bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
        bpy.context.scene.render.filepath = args.output_path + '/render.mkv'
        # Render everything on to the filepath
        bpy.ops.render.render(animation=True)
        # Starts a player automatically to play the output
        bpy.ops.render.play_rendered_anim()
    except:
        print("Error: while rendering the scene.")
    


if __name__ == "__main__":
    main()