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
        "--undistortedImages", dest="undisto_images", metavar='FILE', required=True,
        help="Save the generated file to the specified path",
    )

    parser.add_argument(
        "--outputPath", dest="output_path", metavar='FILE', required=True,
        help="Render an image to the specified path",
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

    if not args.output_path:
        print("Error: --output_path argument not given, aborting.")
        parser.print_help()
        return

    print(args.SFM_cam_path)


    #Clear Current Scene
    try:
        for objects in bpy.data.objects:
            bpy.data.objects.remove(objects)
    except:
        print("Error: While clearing current scene")


    #Place the particle cube

    cube = bpy.data.meshes['Cube']
    objectsCube = bpy.data.objects.new(name="Cube", object_data=cube)

    objectsCube.scale = mathutils.Vector((0.3, 0.3, 0.3))
    objectsCube.location = mathutils.Vector((0, -2.0, -1000))
    bpy.context.scene.collection.objects.link(objectsCube)
    bpy.data.objects['Cube'].hide_set(True)

    # import Undistorted Images

    undis_imgs = []
    #Some of these info will be very useful in the next steps keep them in mind
    number_of_frame = 0
    offset = 0
    image_name = ""
    try:
        files = os.listdir(args.undisto_images)
        for f in files :
            if f.endswith(".exr") and not f.__contains__("UVMap"):
                undis_imgs.append({"name":f})
        number_of_frame = len(undis_imgs)
        image_name = undis_imgs[0]['name']
        offset = int(re.search("_(.*).exr", image_name).group(1)[3:]) - 1

    except:
        print("Error: while importing the undistorted images.")

    #import abc (Animated Camera)
    try:
        bpy.ops.wm.alembic_import(filepath=args.SFM_cam_path)
        animated_cams = bpy.context.selected_editable_objects[:]
        for obj in animated_cams:
            if obj.data and obj.data.type == 'PERSP' and "anim" in obj.data.name:
                bpy.context.scene.collection.objects.link(obj)
                bpy.context.view_layer.objects.active = obj
                bpy.context.scene.camera = obj
                bpy.ops.image.open(filepath=args.undisto_images + "/" + image_name, directory=args.undisto_images, files=undis_imgs, relative_path=True, show_multiview=False)
                bpy.data.cameras[obj.data.name].background_images.new()
                bpy.data.cameras[obj.data.name].show_background_images = True 
                bpy.data.cameras[obj.data.name].background_images[0].image = bpy.data.images[image_name]
                bpy.data.cameras[obj.data.name].background_images[0].frame_method = 'CROP'
                bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_offset = offset
                bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_duration = number_of_frame
                bpy.data.cameras[obj.data.name].background_images[0].image_user.frame_start = 1
                bpy.context.scene.render.film_transparent = True
    except:
        print("Error: while importing the alembic file (Animated Camera).")



    #import abc (Cloud Point)

    try:
        bpy.ops.wm.alembic_import(filepath=args.SFM_Data)
        all_abc_info = bpy.context.selected_editable_objects[:]
        for obj in all_abc_info:
            if obj.name == 'mvgPointCloud.001':
                bpy.context.scene.collection.objects.link(obj)
                bpy.context.view_layer.objects.active = obj
                obj.modifiers.new("ParticleSystem", "PARTICLE_SYSTEM")
                particle_system = bpy.data.particles["ParticleSystem"]
                particle_system.render_type = 'OBJECT'
                
                particle_system.instance_object = bpy.data.objects["Cube"]
                particle_system.emit_from = 'VERT'

                particle_system.count = int(args.Cloud_Point_Density * len(obj.data.vertices.values()))
                particle_system.frame_end = 1.0
                particle_system.use_emit_random = False
                particle_system.particle_size = 0.02
                particle_system.physics_type = 'NO'
                
    except:
        print("Error: while importing the alembic file (Cloud Point).")


    #WE HAVE TO USE THE GRAPH TO MAKE THE BACKGROUND IMAGE VISIBLE (For some reason) All explained in https://www.youtube.com/watch?v=3PoEVlObMv0
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
        bpy.context.scene.node_tree.nodes["Image"].image = bpy.data.images[image_name]

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
        bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
        bpy.context.scene.render.filepath = args.output_path + '/render.mkv'
        bpy.ops.render.render(animation=True)
        bpy.ops.render.play_rendered_anim()
    except:
        print("Error: while rendering the scene.")
    


if __name__ == "__main__":
    main()