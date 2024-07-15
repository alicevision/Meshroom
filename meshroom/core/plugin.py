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

from meshroom.core import desc, hashValue
from meshroom.core import pluginsNodesFolder, pluginsPipelinesFolder, defaultCacheFolder, pluginCatalogFile
from meshroom.core import meshroomFolder
from meshroom.core.graph import loadGraph

#where the executables are (eg meshroom compute)
meshroomBinDir = os.path.abspath(os.path.join(meshroomFolder, "..", "bin"))

class EnvType(Enum):
    """
    enum for the type of env used (by degree of encapsulation)
    """
    NONE = 0
    PIP = 1
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

def _dockerImageExists(image_name, tag='latest'): 
    """
    Check if the desired image:tag exists 
    """
    try: 
        result = subprocess.run( ['docker', 'images', image_name, '--format', '{{.Repository}}:{{.Tag}}'], 
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
    cmd = "conda list --name "+envName
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

def _venvExists(envName):
    """
    Check if the following virtual env exists
    """
    return os.path.isdir(os.path.join(defaultCacheFolder, envName))

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
                    os.symlink(pluginParam.pipelineFolder, os.path.join(pluginsPipelinesFolder, pluginParam.pluginName))
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
    
class PluginNode(desc.Node):
    """
    Class to be used to make a plugin node, you need to overwrite envType and envFile
    """

    @property
    def envType(cls):
        """
        Dynamic env type
        """
        raise NotImplementedError("You must specify one or several envtype in the node description")

    @property
    def envFile(cls):
        """
        Env file used to build the environement, you may overwrite this to custom the behaviour
        """
        raise NotImplementedError("You must specify an env file")

    @property
    def _envName(cls):
        """
        Get the env name by hashing the env files, overwrite this to use a custom pre-build env 
        """
        with open(cls.envFile, 'r') as file:
            envContent = file.read()
        return "meshroom_plugin_"+hashValue(envContent)

    def isBuild(cls):
        """
        Check if the env needs to be build.
        """
        if cls.envType == EnvType.NONE:
            return True
        elif cls.envType == EnvType.PIP:
            #NOTE: could find way to check for installed packages instead of rebuilding all the time
            return False
        elif cls.envType == EnvType.VENV:
            return _venvExists(cls._envName)
        elif cls.envType == EnvType.CONDA:
            return _condaEnvExist(cls._envName)
        elif cls.envType == EnvType.DOCKER:
            return _dockerImageExists(cls._envName)

    def build(cls):
        """
        Perform the needed steps to prepare the environement in which to run the node.
        """
        if cls.envType == EnvType.NONE:
            pass
        elif cls.envType == EnvType.PIP:
            #install packages in the same python as meshroom
            logging.info("Installing packages from "+ cls.envFile)
            buildCommand = sys.executable+" -m pip install "+ cls.envFile
            logging.info("Building with "+buildCommand+" ...")
            returnValue = os.system(buildCommand)
            logging.info("Done")
        elif cls.envType == EnvType.VENV:
            #create venv in default cache folder
            logging.info("Creating virtual env "+os.path.join(defaultCacheFolder, cls._envName)+" from "+cls.envFile)
            envPath = os.path.join(defaultCacheFolder, cls._envName)
            venv.create(envPath, with_pip=True)
            logging.info("Installing dependencies")
            envExe = getVenvExe(envPath)
            returnValue = os.system(_cleanEnvVarsRez()+envExe+" -m pip install -r "+ cls.envFile)
            venvPythonLibFolder = os.path.join(os.path.dirname(envExe), '..', 'lib')
            venvPythonLibFolder = [os.path.join(venvPythonLibFolder, p) 
                                   for p in os.listdir(venvPythonLibFolder) if p.startswith("python")][0]
            os.symlink(meshroomFolder,os.path.join(venvPythonLibFolder, 'site-packages', 'meshroom'))
            logging.info("Done")
        elif cls.envType == EnvType.CONDA:
            #build a conda env from a yaml file
            logging.info("Creating conda env "+cls._envName+" from "+cls.envFile)
            makeEnvCommand = (  _cleanEnvVarsRez()+" conda config --set channel_priority strict ; "
                                +" conda env create -v -v  --name "+cls._envName
                                +" --file "+cls.envFile+" ")
            logging.info("Making conda env")
            logging.info(makeEnvCommand)
            returnValue = os.system(makeEnvCommand)
            #find path to env's folder and add symlink to meshroom
            condaPythonExecudable=subprocess.check_output(_cleanEnvVarsRez()+"conda run -n "+cls._envName
                                                          +" python -c \"import sys; print(sys.executable)\"",   
                                                          shell=True).strip().decode('UTF-8')
            condaPythonLibFolder=os.path.join(os.path.dirname(condaPythonExecudable), '..', 'lib')
            condaPythonLibFolder=[os.path.join(condaPythonLibFolder, p) 
                                  for p in os.listdir(condaPythonLibFolder) if p.startswith("python")][0]
            os.symlink(meshroomFolder,os.path.join(condaPythonLibFolder, 'meshroom'))
            logging.info("Done making conda env")
        elif cls.envType == EnvType.DOCKER:
            #build docker image 
            logging.info("Creating image "+cls._envName+" from "+ cls.envFile)
            buildCommand = "docker build -f "+cls.envFile+" -t "+cls._envName+" "+os.path.dirname(cls.envFile)
            logging.info("Building with "+buildCommand+" ...")
            returnValue = os.system(buildCommand)
            logging.info("Done")
        if returnValue != 0:
            raise RuntimeError("Something went wrong during build")
    
    def getCommandLine(cls, chunk):
        """
        Return the command line needed to enter the environment + meshroom_compute
        Will make meshroom available in the environment.
        """
        if chunk.node.isParallelized:
            raise RuntimeError("Parallelisation not supported for plugin nodes")    
        if chunk.node.graph.filepath == "":
            raise RuntimeError("The project needs to be saved to use plugin nodes")
        saved_graph = loadGraph(chunk.node.graph.filepath)
        if (str(chunk.node) not in [str(f) for f in saved_graph._nodes._objects]
            or chunk.node._uids[0] != saved_graph.findNode(str(chunk.node))._uids[0] ):
            raise RuntimeError("The changes needs to be saved to use plugin nodes")
 
        cmdPrefix = ""
        # vars common to venv and conda, that will be passed when runing conda run or venv
        meshroomCompute= meshroomBinDir+"/meshroom_compute"
        meshroomComputeArgs = "--node "+chunk.node.name+" \""+chunk.node.graph.filepath+"\""
        pythonsetMeshroomPath = "export PYTHONPATH="+meshroomFolder+":$PYTHONPATH;"

        if cls.envType == EnvType.VENV:
            envPath = os.path.join(defaultCacheFolder, cls._envName)
            envExe = getVenvExe(envPath)
            #make sure meshroom in in pythonpath and that we call the right python 
            cmdPrefix = _cleanEnvVarsRez()+pythonsetMeshroomPath+" "+envExe + " "+ meshroomCompute +" " 
        elif cls.envType == EnvType.CONDA:
            #NOTE: system env vars are not passed to conda run, we installed it 'manually' before
            cmdPrefix = _cleanEnvVarsRez()+" conda run --cwd "+os.path.join(meshroomFolder, "..")\
                        +" --no-capture-output -n "+cls._envName+" "+" python "+meshroomCompute
        elif cls.envType == EnvType.DOCKER:
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
            if cls.gpu != desc.Level.NONE:
                runtimeArg="--runtime=nvidia --gpus all"
            #compose cl 
            cmdPrefix = "docker run -it --rm "+runtimeArg+" "+mountCommand+" "+envCommand+" "+cls._envName +" \"python /meshroomBinDir/meshroom_compute "
            meshroomComputeArgs="--node "+chunk.node.name+" "+chunk.node.graph.filepath+"\""

        command=cmdPrefix+" "+meshroomComputeArgs
            
        return command

#class that call command line nodes in an env
class PluginCommandLineNode(PluginNode, desc.CommandLineNode):
    def buildCommandLine(self, chunk):
        cmd = super().buildCommandLine(chunk)
        #the process in Popen does not seem to use the right python, even if meshroom_compute is call within the env
        #so in the case of command line using python, we have to make sur it is using the correct python  
        if self.envType == EnvType.VENV:
            envPath = os.path.join(defaultCacheFolder, self._envName)
            envExe = getVenvExe(envPath)
            cmd=cmd.replace("python", envExe)
        return cmd
