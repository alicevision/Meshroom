__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

class ExportMaya(desc.Node):

    category = 'Export'
    documentation = '''
    Export a Maya script.
    This script executed inside Maya, will gather the Meshroom computed elements.
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="alembic",
            label="Alembic File",
            description="Input alembic file.",
            value="",
        ),
        desc.File(
            name="mesh",
            label="Input Mesh",
            description="Input mesh file.",
            value="",
        ),
        desc.File(
            name="images",
            label="Undistorted Images",
            description="Undistorted images template.",
            value="",
        ),
        desc.BoolParam(
            name="generateMaya",
            label="Generate Maya Scene",
            description="Select to generate the Maya scene in addition to the export of the mel script.",
            value=True,
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
            name="meloutput",
            label="Mel Script",
            description="Generated mel script.",
            value="{nodeCacheFolder}/import.mel",
        ),
        desc.File(
            name="mayaoutput",
            label="Maya Scene",
            description="Generated Maya scene.",
            value="{nodeCacheFolder}/scene.mb",
            enabled=lambda node: node.generateMaya.value,
        ),
    ]

    def processChunk(self, chunk):
        
        import pyalicevision
        import pathlib
        import inspect
        import subprocess

        chunk.logManager.start(chunk.node.verboseLevel.value)
        
        chunk.logger.info("Open input file")
        data = pyalicevision.sfmData.SfMData()
        ret = pyalicevision.sfmDataIO.load(data, chunk.node.input.value, pyalicevision.sfmDataIO.ALL)
        if not ret:
            chunk.logger.error("Cannot open input")
            chunk.logManager.end()
            raise RuntimeError()

        #Check that we have Only one intrinsic
        intrinsics = data.getIntrinsics()
        if len(intrinsics) > 1:
            chunk.logger.error("Only project with a single intrinsic are supported")
            chunk.logManager.end()
            raise RuntimeError()

        intrinsicId = next(iter(intrinsics))
        intrinsic = intrinsics[intrinsicId]
        w = intrinsic.w()
        h = intrinsic.h()

        cam = pyalicevision.camera.Pinhole.cast(intrinsic)
        if cam == None:
            chunk.logger.error("Intrinsic is not a required pinhole model")
            chunk.logManager.end()
            raise RuntimeError()

        offset = cam.getOffset()
        pix2inches = cam.sensorWidth() / (25.4 * max(w, h));
        ox = -pyalicevision.numeric.getX(offset) * pix2inches
        oy = pyalicevision.numeric.getY(offset) * pix2inches

        scale = cam.getScale()
        fx = pyalicevision.numeric.getX(scale)
        fy = pyalicevision.numeric.getY(scale)


        #Retrieve the first frame

        minIntrinsicId = 0
        minFrameId = 0
        minFrameName = ''
        first = True
        views = data.getViews()
        
        for viewId in views:
            
            view = views[viewId]
            frameId = view.getFrameId()
            intrinsicId = view.getIntrinsicId()
            frameName = pathlib.Path(view.getImageInfo().getImagePath()).stem

            if first or frameId < minFrameId:
                minFrameId = frameId
                minIntrinsicId = intrinsicId
                minFrameName = frameName
                first = False
        

        #Generate the script itself
        mayaFileName = chunk.node.mayaoutput.value
        header = f'''
        file -f -new;
        '''

        footer = f'''
        file -rename "{mayaFileName}";
        file -type "mayaBinary";
        file -save;
        '''
        
        alembic = chunk.node.alembic.value
        abcString = f'AbcImport -mode open -fitTimeRange "{alembic}";'

        mesh = chunk.node.mesh.value
        objString = f'file -import -type "OBJ"  -ignoreVersion -ra true -mbl true -mergeNamespacesOnClash false -namespace "mesh" -options "mo=1"  -pr  -importTimeRange "combine" "{mesh}";'

        framePath = chunk.node.images.value.replace('<INTRINSIC_ID>', str(minIntrinsicId)).replace('<FILESTEM>', minFrameName)

        camString = f'''
        select -r mvgCameras ;
        string $camName[] = `listRelatives`;

        currentTime {minFrameId};

        imagePlane -c $camName[0] -fileName "{framePath}";
        
        setAttr "imagePlaneShape1.useFrameExtension" 1;
        setAttr "imagePlaneShape1.offsetX" {ox};
        setAttr "imagePlaneShape1.offsetY" {oy};
        '''

        ipa = fx / fy
        advCamString = ''

        if abs(ipa - 1.0)  < 1e-6:
            advCamString = f'''
            setAttr "imagePlaneShape1.fit" 1;
            '''
        else:
            advCamString = f'''
            setAttr "imagePlaneShape1.fit" 4;
            setAttr "imagePlaneShape1.squeezeCorrection" {ipa};
            
            select -r $camName[0];
            float $vaperture = `getAttr ".verticalFilmAperture"`;
            float $scaledvaperture = $vaperture * {ipa};
            setAttr "imagePlaneShape1.sizeY" $scaledvaperture;
            '''

        with open(chunk.node.meloutput.value, "w") as f:
            if chunk.node.generateMaya.value:
                f.write(inspect.cleandoc(header) + '\n')
            f.write(inspect.cleandoc(abcString) + '\n')
            f.write(inspect.cleandoc(objString) + '\n')
            f.write(inspect.cleandoc(camString) + '\n')
            f.write(inspect.cleandoc(advCamString) + '\n')
            if chunk.node.generateMaya.value:
                f.write(inspect.cleandoc(footer) + '\n')

        chunk.logger.info("Mel Script generated")
        
        #Export to maya
        if chunk.node.generateMaya.value:
            try:
                melPath = chunk.node.meloutput.value
                cmd = f'maya_batch -batch -script "{melPath}"'
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()

                if len(stdout) > 0:
                    chunk.logger.info(stdout.decode())

                rc = p.returncode
                if rc != 0:
                    chunk.logger.error(stderr.decode())
                    raise Exception(rc)

            except Exception as e:
                chunk.logger.error('Failed to run maya batch : "{}".'.format(str(e)))
                raise RuntimeError()
            
            chunk.logger.info("Maya Scene generated")

        chunk.logManager.end()
