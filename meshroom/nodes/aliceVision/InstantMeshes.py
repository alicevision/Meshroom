# Instant Meshes plugin v.0.1-0.4 by Jörg Dittmer (https://github.com/djoerg) 02-03.2020,
# based on the plugin by natowi (https://github.com/natowi) 11.2019
#
# Wavefront OBJ format load/save routine is inspired by James Gregson's blog post: 
# http://jamesgregson.ca/loadsave-wavefront-obj-files-in-python.html
#

__version__ = "0.4"

from meshroom.core import desc

import os
import numpy as np
from pymeshfix import _meshfix

from typing import List, Tuple
        

class InstantMeshes(desc.CommandLineNode):
    commandLine = 'external_instantMeshes {inputMeshValue} -S {smoothValue} %params% -o {outputInstantMeshesValue}'

    cpu = desc.Level.NORMAL
    ram = desc.Level.NORMAL

# documentation = '''Instant Meshes is an auto-retopology tool that can be used to remesh a surface into an isotropic triangular or quad-dominant mesh.'''

    inputs = [
        desc.File(
            name="inputMesh", label='Input Mesh',
            description='Input mesh (OBJ/PLY file format).',
            value='',
            uid=[0],
            ),
        desc.IntParam(
            name='threads', label='Threads',
            description="Number of threads used for parallel computations.\n"
                        " * 0: let InstantMeshes decide.",
            value=0,
            range=(0, 32, 1),
            uid=[],
            advanced=True
            ),
        desc.BoolParam(
            name='deterministic', label='Deterministic',
            description='Prefer (slower) deterministic algorithms.',
            value=False,
            uid=[0],
            advanced=True
            ),                        
        desc.ChoiceParam(
            name='remeshMode', label='Remesh Mode',
            description='The remeshing mode.',
            value='Triangles',
            values=('Triangles', 'Quads (2/4)', 'Quads (4/4)'),
            exclusive=True,
            uid=[0],
            ),
        desc.BoolParam(
            name='intrinsic', label='Intrinsic',
            description='Use an extrinsic or intrinsic smoothness energy with automatic parameter-free alignment to geometric features.',
            value=False,
            uid=[0]
            ),
		desc.IntParam(
            name='crease', label='Crease angle',
            description="Dihedral angle threshold for creases in degrees.\n"
                        " * -1: don't use creases.",
            value=-1,
            range=(-1, 90, 1),
            uid=[0],
            ),
        desc.IntParam(
            name='smooth', label='Smoothing iterations',
            description='To increase the mesh uniformity, Laplacian smoothing and reprojection steps can be performed as a post process.',
            value=2,
            range=(0, 10, 1),
            uid=[0],
            ),
        desc.BoolParam(
            name='fixMesh', label='Fix Mesh',
            description="Use MeshFix (a great tool by Marco Attene) to repair defect faces.\n"
                        " * removes self-intersections\n"
                        " * sometimes, removes non-manifolds too\n"
                        "\n"
                        "Thanks to Alex Kaszynski for providing the python wrapper PyMeshFix.",
            value=True,
            uid=[0]
            ),

    ]

    outputs = [
        desc.File(
            name="outputMesh", label="Output mesh",
            description="Output mesh (OBJ file format).",
            value=desc.Node.internalFolder + 'mesh.obj',
            uid=[],
            ),
        desc.File(
            name="outputInstantMeshes", label="Output Instant Meshes",
            description="Unmodified output from Instant Meshes (OBJ file format).\n"
                        "Warning: This output isn't compatible with Meshroom and can cause\n"
                        "         crashes or unexpected behaviour if feed directly into a node!\n"
                        "         (Of course, you CAN use the Publish node to export it.)",
            value=desc.Node.internalFolder + 'mesh_im.obj',
            uid=[],
            ),

    ]

    
    def buildCommandLine(self, chunk):
        """Builds the complex cli params and replaces %params% token in commandline-string."""
        params = ''
        cn = chunk.node
        
        if cn.remeshMode.value == 'Triangles'  : params += " -r 6 -p 6"
        if cn.remeshMode.value == 'Quads (2/4)': params += " -r 2 -p 4"
        if cn.remeshMode.value == 'Quads (4/4)': params += " -r 4 -p 4"
        
        if cn.threads.value > 0: params += " -t " + cn.threads.value
        if cn.deterministic.value == True: params += " -d"
        
        if cn.intrinsic.value == True: params += " -i"
        if cn.crease.value >= 0: params += " -c " + str(cn.crease.value)
        
        cmd = desc.CommandLineNode.buildCommandLine(self, chunk)
        cmd = cmd.replace("%params%", params, 1)
        
        return cmd
    
    
    def processChunk(self, chunk):
        """Processes one Chunk, converts Obj format and optionaly fixes self-intersections."""
        print("processChunk")
        
        # executes commandline running Instant Meshes
        desc.CommandLineNode.processChunk(self, chunk)
        
        # load Instant Meshes output Obj file
        mesh = Mesh.createFromFile(chunk.node.outputInstantMeshes.value)
        print("Mesh loaded")
        
        # fix self-intersections by utilizing MeshFix tool by Marco Attene
        if chunk.node.fixMesh.value:
            mesh.fixSelfIntersections()
            print("Mesh fixed")
            
        # save Meshroom compliant Obj file
        mesh.save(chunk.node.outputMesh.value)
        print("Mesh saved")

        

# globaly defined type aliases (for now, only used in class 'Mesh')        
Vector = Tuple[float, float, float]
Ngon = List[int]
#Color = Tuple[int, int, int]

class Mesh(object):

    def __init__(self):
        self.path: str                   = None # remember path of loaded object
        self.triangulate: bool           = True # use triangulation in _addFace()
        
        self.vertices: List[Vector]      = []   # vertices as an Nx3 or Nx6 array (per vtx colors)
        self.faces: List[Ngon]           = []   # N*x array, x=# of vertices, stored as vid (-1 for N/A)

        # TODO: implement vertex colors
        # self.vertex_colors: List[Color] = []   # vertices as an Nx3 (per vtx colors)

        self.texcoords: List[Vector]     = []   # texture coordinates
        self.normals: List[Vector]       = []   # normal vectors
        self.faceTexcoords: List[Ngon]   = []   # N*x array, x=# of texture-coords, stored as tid (-1 for N/A)
        self.faceNormals: List[Ngon]     = []   # N*x array, x=# of normals, stored as nid (-1 for N/A)

        
    @classmethod
    def createFromFile(cls, filename: str, triangulate: bool = None) -> 'Mesh':
        """Alternative constructor loading mesh from file."""
        mesh = cls()
        mesh.triangulate = mesh.triangulate if triangulate is None else triangulate
        mesh.load(filename)
        return mesh
        

    def _addFace(self, vids: Ngon, tids: Ngon = None, nids: Ngon = None) -> None:
        """Adds a face to the self.faces list, trangulates it if requested."""
        
        # TODO: implement handling of texture-coords and normals
        
        if len(vids) > 3 and self.triangulate:
            # simple fan-like triangulation (works only for convex polys!)
            # TODO: implement better triangulation
            for i in range(2, len(vids)):
                self.faces.append([vids[0], vids[i-1], vids[i]])
        else:
            self.faces.append(vids)

            
    def load(self, filename: str) -> None:
        """Dispatcher method calls matching _loadXxx() method by file extension."""

        self.path = filename
        
        ext = os.path.splitext(filename)[1][1:]
        methodname = '_load' + ext.capitalize()
        
        try:
            method = getattr(self, methodname)
        except AttributeError:
            print("Loading file type '." +ext+ "' not implemented yet!")
            raise
        
        method(filename) # calls loadXxx() method on instance

        
    def _loadObj(self, filename: str) -> None:
        """Reads a Wavefront .obj file from disk.

        Handles only very rudimentary reading and contains no error handling!

        Does not handle:
            - relative indexing
            - subobjects or groups
            - lines, splines, beziers, etc.
        """
        # parses one face-vertex record as either vid, vid/tid, vid//nid or vid/tid/nid
        # and returns a 3-tuple where unparsed values are replaced with -1
        def parsePolyVertex( vstr: str ) -> Ngon:
            vals = vstr.split('/')
            vid = int(vals[0])-1
            tid = int(vals[1])-1 if len(vals) > 1 and vals[1] else -1
            nid = int(vals[2])-1 if len(vals) > 2 else -1
            return (vid,tid,nid)

        # parses one face record 
        # and returns 3-tuple containing vids,tids,nids
        def parsePolygon(toks: List[str]) -> Tuple[Ngon, Ngon, Ngon]:
            vids, tids, nids = ([], [], []);
            for vstr in toks[1:]:
                vid,tid,nid = parsePolyVertex(vstr)
                vids.append(vid)
                tids.append(tid)
                nids.append(nid)
            return (vids, tids, nids)      
        
        with open( filename, 'r' ) as objfile:
            for line in objfile:
                toks = line.split()
                if not toks:
                    continue
                if toks[0] == 'v':
                    self.vertices.append( [ float(v) for v in toks[1:]] )
                elif toks[0] == 'vn':
                    self.normals.append( [ float(v) for v in toks[1:]] )
                elif toks[0] == 'vt':
                    self.texcoords.append( [ float(v) for v in toks[1:]] )
                elif toks[0] == 'f':
                    vids, tids, nids = parsePolygon(toks)
                    self._addFace(vids, tids, nids)

        
    def save(self, filename: str, texcoords: bool = False, normals: bool = False) -> None:
        """Dispatcher method calls matching _saveXxx() method by file extension."""
        
        ext = os.path.splitext(filename)[1][1:]
        methodname = '_save' + ext.capitalize()
        
        try:
            method = getattr(self, methodname)
        except AttributeError:
            print("Saving file type '." +ext+ "' not implemented yet!")
            raise
        
        method(filename, texcoords, normals)  # calls saveXxx() method on instance


    def _saveObj(self, filename: str, texcoords: bool = False, normals: bool = False) -> None:
        """Saves a Wavefront .obj file to disk.
        
        Warning: Contains no error checking!
        """
        with open( filename, 'w' ) as ofile:
        
            if texcoords:
                assert len(self.faces) == len(self.faceTexcoords), "Number of texcoord-ids must match number of vertex-ids"

            if normals:
                assert len(self.faces) == len(self.faceNormals), "Number of normal-ids must match number of vertex-ids"
                
            # write header
            ofile.write("#\n")
            ofile.write("# Wavefront OBJ file\n")
            ofile.write("# Created by InstantMeshes node\n")
            ofile.write("#\n")
        
            # write vertices
            for vtx in self.vertices:
                ofile.write('v '+' '.join(['{}'.format(v) for v in vtx])+'\n')
            # write texcoords
            if texcoords:
                for tex in self.texcoords:
                    ofile.write('vt '+' '.join(['{}'.format(vt) for vt in tex])+'\n')
            # write normals
            if normals:
                for nrm in self.normals:
                    ofile.write('vn '+' '.join(['{}'.format(vn) for vn in nrm])+'\n')
                    
                    
            # write faces
            print("Saving poly count: " + str(len(self.faces)))
                                
            for pid in range(0, len(self.faces)):                    
                pstr = 'f'
            
                for v in range(0, len(self.faces[pid])):
                    pstr += ' '
                    pstr += str(self.faces[pid][v] + 1)
                    if texcoords or normals:
                        pstr += '/'
                        if texcoords and self.faceTexcoords[pid][v] > -1:
                            pstr += str(self.faceTexcoords[pid][v] + 1)
                    if normals:
                        pstr += '/' + str(self.faceNormals[pid][v] + 1 if self.faceNormals[pid][v] > -1 else '')
                ofile.write(pstr + '\n')


    def fixSelfIntersections(self):
        """Uses PyMeshFix to cleanup self-intersections, and sometimes non-manifolds."""
        
        # convert vertex/face lists to numpy-arrays 
        v = np.asarray(self.vertices, np.float)
        f = np.asarray(self.faces, np.int)
        assert v.ndim == 2, 'Vertex array must be 2D'
        assert v.shape[1] == 3, 'Vertex array must contain three columns'
        assert f.ndim == 2, 'Face array must be 2D'
        assert f.shape[1] == 3, 'Face array must contain three columns'
        
        # create meshfix triangle mesh object
        tmesh= _meshfix.PyTMesh()
        tmesh.load_array(v, f)
        
        # clean mesh (should remove self-intersections and non-manifolds)
        tmesh.clean(max_iters=10, inner_loops=3)
        
        # get vertex/face numpy-arrays and convert back to lists 
        v, f = tmesh.return_arrays()
        self.vertices = v.tolist()
        self.faces = f.tolist()
                
        
