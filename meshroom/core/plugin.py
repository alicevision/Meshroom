#!/usr/bin/env python
# coding:utf-8

"""
This file defines the nodes and logic needed for the plugin system in meshroom.
A plugin is a collection of node(s) of any type with their rutime environnement setup file attached.
We use the term 'environment' to abstract a docker container or a conda/virtual environment.
"""

from enum import Enum
import json
import os, sys
import logging
import urllib
from distutils.dir_util import copy_tree, remove_tree
import subprocess 
import venv
import inspect

from meshroom.core import desc
from meshroom.core import pluginsNodesFolder, pluginsPipelinesFolder, pluginCatalogFile, defaultCacheFolder
from meshroom.core import meshroomFolder
from meshroom.core.graph import loadGraph
from meshroom.core import hashValue

#executables def
meshroomBinDir = os.path.abspath(os.path.join(meshroomFolder, "..", "bin"))
condaBin = "conda"
dockerBin = "docker"

class EnvType(Enum):
    """
    enum for the type of env used (by degree of encapsulation)
    """
    NONE = 0
    PIP = 1
    REZ = 2
    VENV = 10
    CONDA = 20
    DOCKER = 30

#NOTE: could add the concept of dependencies between plugins
class PluginParams():
    """"
    Class that holds parameters to install one plugin from a folder and optionally from a json structure
    """
    def __init__(self, pluginUrl, jsonData=None):
        #get the plugin name from folder
        self.pluginName = os.path.basename(pluginUrl)
        #default node and pipeline locations
        self.nodesFolder = os.path.join(pluginUrl, "meshroomNodes")
        self.pipelineFolder = os.path.join(pluginUrl, "meshroomPipelines")
        #overwrite is json is passed
        if jsonData is not None:
            self.pluginName = jsonData["pluginName"]
            #default node and pipeline locations
            self.nodesFolder = os.path.join(pluginUrl, jsonData["nodesFolder"])
            if "pipelineFolder" in jsonData.keys():
                self.pipelineFolder = os.path.join(pluginUrl, jsonData["pipelineFolder"])

def getEnvName(envContent):
    return "meshroom_plugin_"+hashValue(envContent)

def _dockerImageExists(image_name, tag='latest'): 
    """
    Check if the desired image:tag exists 
    """
    try: 
        result = subprocess.run( [dockerBin, 'images', image_name, '--format', '{{.Repository}}:{{.Tag}}'], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True )
        if result.returncode != 0: 
            return False 
        images = result.stdout.splitlines() 
        image_tag = f"{image_name}:{tag}" 
        return image_tag in images 
    except Exception as e: 
        return False 

def _cleanEnvVarsRez():
    """
    Used to unset all rez defined env that mess up with conda.
    """
    cmd = "unset python; unset PYTHONPATH; "
    return cmd

def _condaEnvExist(envName):
    """
    Checks if a specified env exists
    """
    cmd = condaBin+" list --name "+envName
    return os.system(cmd) == 0    

def _formatPluginName(pluginName):
    """
    Replaces spaces for env naming
    """
    return pluginName.replace(" ", "_")

def getVenvExe(venvPath):
    """
    Returns the path for the python in a virtual env 
    """
    if not os.path.isdir(venvPath):
        raise ValueError("The specified path "+venvPath+" is not a directory")
    if sys.platform == "win32":
        executable = os.path.join(venvPath, 'Scripts', 'python.exe')
    else:
        executable = os.path.join(venvPath, 'bin', 'python')
    if not os.path.isfile(executable):
        raise FileNotFoundError(f"Python executable not found in the specified virtual environment: "+executable)
    return executable

def getVenvPath(envName):
    return os.path.join(defaultCacheFolder, envName)

def _venvExists(envName):
    """
    Check if the following virtual env exists
    """
    return os.path.isdir(getVenvPath(envName))

def getActiveRezPackages():
    """
    Returns a list containing the active explicit packages
    """
    packages = []
    if 'REZ_REQUEST' in os.environ:
        nondefpackages = [n.split("-")[0] for n in os.environ.get('REZ_REQUEST', '').split()]
        resolvedPackages = os.environ.get('REZ_RESOLVE', '').split()
        resolvedVersions = {}
        for r in resolvedPackages:
            if r.startswith('~'):
                continue
            v = r.split('-')
            resolvedVersions[v[0]] = v[1]
        packages = [p+"-"+resolvedVersions[p] for p in resolvedVersions.keys() if p in nondefpackages]
    return packages

def installPlugin(pluginUrl):
    """
    Install plugin from an url or local path.
    Regardless of the method, the content will be copied in the plugin folder of meshroom (which is added to the list of directory to load nodes from).
    There are two options :
        - having the following structure :
            - [plugin folder] (will be the plugin name)
                - meshroomNodes
                    - [code for your nodes] that contains relative path to a DockerFile|env.yaml|requirements.txt
                    - [...]
                - meshroomPipelines
                    - [your meshroom templates]
        - having a meshroomPlugin.json file at the root of the plugin folder
          With this solution, you may have several separate node folders.
    """
    logging.info("Installing plugin from "+pluginUrl)
    try:
        isLocal = True
        #if git repo, clone the repo in cache
        if urllib.parse.urlparse(pluginUrl).scheme in ('http', 'https','git'):
            os.chdir(defaultCacheFolder)
            os.system("git clone "+pluginUrl)
            pluginName = pluginUrl.split('.git')[0].split('/')[-1]
            pluginUrl = os.path.join(defaultCacheFolder, pluginName)
            isLocal = False
        #sanity check
        if not os.path.isdir(pluginUrl):
            ValueError("Invalid plugin path :"+pluginUrl)
        #by default only one plugin, and with default file hierachy
        pluginParamList=[PluginParams(pluginUrl)]
        #location of the json file if any
        paramFile=os.path.join(pluginUrl, "meshroomPlugin.json")
        #load json for custom install if any
        if os.path.isfile(paramFile):
            jsonData=json.load(open(paramFile,"r"))
            pluginParamList = [PluginParams(pluginUrl, jsonDataplugin) for jsonDataplugin in jsonData]
        #for each plugin, run the 'install'
        for pluginParam in pluginParamList:
            intallFolder = os.path.join(pluginsNodesFolder, _formatPluginName(pluginParam.pluginName))
            logging.info("Installing "+pluginParam.pluginName+" from "+pluginUrl+" in "+intallFolder)
            #check if folder valid
            if not os.path.isdir(pluginParam.nodesFolder):
                raise RuntimeError("Invalid node folder: "+pluginParam.nodesFolder)
            #check if already installed
            if os.path.isdir(intallFolder):
                logging.warn("Plugin already installed, will overwrite")
                if os.path.islink(intallFolder):
                    os.unlink(intallFolder)
                else:
                    remove_tree(intallFolder)
            #install via symlink if local, otherwise copy (usefull to develop)
            if isLocal:
                os.symlink(pluginParam.nodesFolder, intallFolder)
                if os.path.isdir(pluginParam.pipelineFolder):
                    pipelineFolderLink = os.path.join(pluginsPipelinesFolder, pluginParam.pluginName)
                    if os.path.exists(pipelineFolderLink):
                        logging.warn("Plugin already installed, will overwrite")
                        os.unlink(pipelineFolderLink)
                    os.symlink(pluginParam.pipelineFolder, pipelineFolderLink)
            else:
                copy_tree(pluginParam.nodesFolder, intallFolder)
                if os.path.isdir(pluginParam.pipelineFolder):
                    copy_tree(pluginParam.pipelineFolder, os.path.join(pluginsPipelinesFolder, pluginParam.pluginName))
        #remove repo if was cloned
        if not isLocal:
            os.removedirs(pluginUrl)
        #NOTE: could try to auto load the plugins to avoid restart and test files
    except Exception as ex:
        logging.error(ex)
        return False
        
    return True

def getCatalog():
    """
    Returns the plugin catalog
    """
    jsonData=json.load(open(pluginCatalogFile,"r"))
    return jsonData
        
def getInstalledPlugin():
    """
    Returns the list of installed plugins
    """
    installedPlugins = [os.path.join(pluginsNodesFolder, f) for f in os.listdir(pluginsNodesFolder)]
    return installedPlugins

def uninstallPlugin(pluginUrl):
    """
    Uninstall a plugin
    """
    #NOTE: could also remove the env files
    if not os.path.exists(pluginUrl):
        raise RuntimeError("Plugin "+pluginUrl+" is not installed")
    if os.path.islink(pluginUrl):
        os.unlink(pluginUrl)
    else:
        os.removedirs(pluginUrl) 

def isBuilt(nodeDesc):
    """
    Check if the env needs to be build for a specific nodesc.
    """
    if nodeDesc.envType in [EnvType.NONE, EnvType.REZ]:
        return True
    elif nodeDesc.envType == EnvType.PIP:
        #NOTE: could find way to check for installed packages instead of rebuilding all the time
        return False
    elif nodeDesc.envType == EnvType.VENV:
        return _venvExists(nodeDesc._envName)
    elif nodeDesc.envType == EnvType.CONDA:
        return _condaEnvExist(nodeDesc._envName)
    elif nodeDesc.envType == EnvType.DOCKER:
        return _dockerImageExists(nodeDesc._envName)

def build(nodeDesc):
    """
    Perform the needed steps to prepare the environement in which to run the node.
    """
    if not hasattr(nodeDesc, 'envFile'):
        raise RuntimeError("The nodedesc has no env file")
    returnValue = 0
    if nodeDesc.envType in [EnvType.NONE, EnvType.REZ]:
        pass
    elif nodeDesc.envType == EnvType.PIP:
        #install packages in the same python as meshroom
        logging.info("Installing packages from "+ nodeDesc.envFile)
        buildCommand = sys.executable+" -m pip install "+ nodeDesc.envFile
        logging.info("Building with "+buildCommand+" ...")
        returnValue = os.system(buildCommand)
        logging.info("Done")
    elif nodeDesc.envType == EnvType.VENV:
        #create venv in default cache folder
        envPath = getVenvPath(nodeDesc._envName)
        logging.info("Creating virtual env "+envPath+" from "+nodeDesc.envFile)
        venv.create(envPath, with_pip=True)
        logging.info("Installing dependencies")
        envExe = getVenvExe(envPath)
        returnValue = os.system(_cleanEnvVarsRez()+envExe+" -m pip install -r "+ nodeDesc.envFile)
        venvPythonLibFolder = os.path.join(os.path.dirname(envExe), '..', 'lib')
        venvPythonLibFolder = [os.path.join(venvPythonLibFolder, p) 
                                for p in os.listdir(venvPythonLibFolder) if p.startswith("python")][0]
        os.symlink(meshroomFolder,os.path.join(venvPythonLibFolder, 'site-packages', 'meshroom'))
        logging.info("Done")
    elif nodeDesc.envType == EnvType.CONDA:
        #build a conda env from a yaml file
        logging.info("Creating conda env "+nodeDesc._envName+" from "+nodeDesc.envFile)
        makeEnvCommand = (  _cleanEnvVarsRez()+condaBin+" config --set channel_priority strict ; "
                            +condaBin+"  env create -v -v  --name "+nodeDesc._envName
                            +" --file "+nodeDesc.envFile+" ")
        logging.info("Making conda env")
        logging.info(makeEnvCommand)
        returnValue = os.system(makeEnvCommand)
        #find path to env's folder and add symlink to meshroom
        condaPythonExecudable=subprocess.check_output(_cleanEnvVarsRez()+condaBin+" run -n "+nodeDesc._envName
                                                        +" python -c \"import sys; print(sys.executable)\"",   
                                                        shell=True).strip().decode('UTF-8')
        condaPythonLibFolder=os.path.join(os.path.dirname(condaPythonExecudable), '..', 'lib')
        condaPythonLibFolder=[os.path.join(condaPythonLibFolder, p) 
                                for p in os.listdir(condaPythonLibFolder) if p.startswith("python")][0]
        os.symlink(meshroomFolder,os.path.join(condaPythonLibFolder, 'meshroom'))
        logging.info("Done making conda env")
    elif nodeDesc.envType == EnvType.DOCKER:
        #build docker image 
        logging.info("Creating image "+nodeDesc._envName+" from "+ nodeDesc.envFile)
        buildCommand = dockerBin+" build -f "+nodeDesc.envFile+" -t "+nodeDesc._envName+" "+os.path.dirname(nodeDesc.envFile)
        logging.info("Building with "+buildCommand+" ...")
        returnValue = os.system(buildCommand)
        logging.info("Done")
    else:
        raise RuntimeError("Invalid env type")
    if returnValue != 0:
        raise RuntimeError("Something went wrong during build")

def getCommandLine(chunk):
    """
    Return the command line needed to enter the environment + meshroom_compute
    Will make meshroom available in the environment.
    """
    nodeDesc=chunk.node.nodeDesc
    if chunk.node.isParallelized:
        raise RuntimeError("Parallelisation not supported for plugin nodes")    
    if chunk.node.graph.filepath == "":
        raise RuntimeError("The project needs to be saved to use plugin nodes")
    saved_graph = loadGraph(chunk.node.graph.filepath)
    if (str(chunk.node) not in [str(f) for f in saved_graph._nodes._objects]
        or chunk.node._uid != saved_graph.findNode(str(chunk.node))._uid ):
        raise RuntimeError("The changes needs to be saved to use plugin nodes")

    cmdPrefix = ""
    # vars common to venv and conda, that will be passed when runing conda run or venv
    meshroomCompute= meshroomBinDir+"/meshroom_compute"
    meshroomComputeArgs = "--node "+chunk.node.name+" \""+chunk.node.graph.filepath+"\""
    pythonsetMeshroomPath = "export PYTHONPATH="+meshroomFolder+":$PYTHONPATH;"

    if nodeDesc.envType == EnvType.VENV:
        envPath = getVenvPath(nodeDesc._envName)
        envExe = getVenvExe(envPath)
        #make sure meshroom in in pythonpath and that we call the right python 
        cmdPrefix = _cleanEnvVarsRez()+pythonsetMeshroomPath+" "+envExe + " "+ meshroomCompute +" " 
    elif nodeDesc.envType == EnvType.REZ:
        cmdPrefix = "rez env "+" ".join(getActiveRezPackages())+" "+nodeDesc._envName+" -- "+ meshroomCompute +" " 
    elif nodeDesc.envType == EnvType.CONDA:
        #NOTE: system env vars are not passed to conda run, we installed it 'manually' before
        cmdPrefix = _cleanEnvVarsRez()+condaBin+"  run --cwd "+os.path.join(meshroomFolder, "..")\
                    +" --no-capture-output -n "+nodeDesc._envName+" "+" python "+meshroomCompute
    elif nodeDesc.envType == EnvType.DOCKER:
        #path to the selected plugin
        classFile=inspect.getfile(chunk.node.nodeDesc.__class__)
        pluginDir = os.path.abspath(os.path.realpath(os.path.join(os.path.dirname(classFile),"..")))
        #path to the project/cache
        projectDir=os.path.abspath(os.path.realpath(os.path.dirname(chunk.node.graph.filepath)))
        mountCommand = (' --mount type=bind,source="'+projectDir+'",target="'+projectDir+'"' #mount with same file hierarchy
                        +' --mount type=bind,source="'+pluginDir+'",target=/meshroomPlugin,readonly' #mount the plugin folder (because of symbolic link, not necesseraly physically in meshroom's folder)
                        +' --mount type=bind,source="'+meshroomFolder+'",target=/meshroomFolder/meshroom,readonly' 
                        +' --mount type=bind,source="'+meshroomBinDir+'",target=/meshroomBinDir,readonly')
        #adds meshroom's code(& the plugin actual path that can be different (because of the dymbolic link)) to the python path
        envCommand = " --env PYTHONPATH=/meshroomFolder --env MESHROOM_NODES_PATH=/meshroomPlugin"
        #adds the gpu arg if needed
        runtimeArg=""
        if chunk.node.nodeDesc.gpu != desc.Level.NONE:
            runtimeArg="--runtime=nvidia --gpus all"
        #compose cl 
        cmdPrefix = dockerBin+" run -it --rm "+runtimeArg+" "+mountCommand+" "+envCommand+" "+nodeDesc._envName +" \"python /meshroomBinDir/meshroom_compute "
        meshroomComputeArgs="--node "+chunk.node.name+" "+chunk.node.graph.filepath+"\""
    else:
        raise RuntimeError("NodeType not recognised")

    command=cmdPrefix+" "+meshroomComputeArgs
        
    return command

# you may use these to explicitly define Pluginnodes
class PluginNode(desc.Node):
    pass

class PluginCommandLineNode(desc.CommandLineNode):
    pass