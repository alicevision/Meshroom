__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import glob
import os
import json
import zipfile
import requests
import io


class BufferReader(io.BytesIO): # object to call the callback while the file is being uploaded
    def __init__(self, buf=b'',
                 callback=None,
                 cb_args=(),
                 cb_kwargs={},
                 stopped=None):
        self._callback = callback
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs
        self._stopped = stopped
        self._progress = 0
        self._len = len(buf)
        io.BytesIO.__init__(self, buf)

    def __len__(self):
        return self._len

    def read(self, n=-1):
        chunk = io.BytesIO.read(self, n)
        self._progress += int(len(chunk))
        self._cb_kwargs.update({
            'size'    : self._len,
            'progress': self._progress
        })
        if self._callback:
            try:
                self._callback(*self._cb_args, **self._cb_kwargs)
            except Exception as e: # catches exception from the callback
                self._cb_kwargs['logManager'].logger.warning('Error at callback: {}'.format(e))

        if self._stopped():
            raise RuntimeError('Node stopped by user')
        return chunk

def progressUpdate(size=None, progress=None, logManager=None):
    if not logManager.progressBar:
        logManager.makeProgressBar(size, 'Upload progress:')

    logManager.updateProgressBar(progress)

class SketchfabUpload(desc.Node):
    size = desc.DynamicNodeSize('inputFiles')

    category = 'Export'
    documentation = '''
Upload a textured mesh on Sketchfab.
'''

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="input",
                label="Input",
                description="",
                value="",
            ),
            name="inputFiles",
            label="Input Files",
            description="Input Files to export.",
            group="",
        ),
        desc.StringParam(
            name="apiToken",
            label="API Token",
            description="Get your token from https://sketchfab.com/settings/password.",
            value="",
        ),
        desc.StringParam(
            name="title",
            label="Title",
            description="Title cannot be longer than 48 characters.",
            value="",
        ),
        desc.StringParam(
            name="description",
            label="Description",
            description="Description cannot be longer than 1024 characters.",
            value="",
        ),
        desc.ChoiceParam(
            name="license",
            label="License",
            description="License label.",
            value="CC Attribution",
            values=["CC Attribution",
                    "CC Attribution-ShareAlike",
                    "CC Attribution-NoDerivs",
                    "CC Attribution-NonCommercial",
                    "CC Attribution-NonCommercial-ShareAlike",
                    "CC Attribution-NonCommercial-NoDerivs"],
        ),
        desc.ListAttribute(
            elementDesc=desc.StringParam(
                name="tag",
                label="Tag",
                description="Tag cannot be longer than 48 characters.",
                value="",
            ),
            name="tags",
            label="Tags",
            description="Maximum of 42 separate tags.",
            group="",
        ),
        desc.ChoiceParam(
            name="category",
            label="Category",
            description="Adding categories helps improve the discoverability of your model.",
            value="none",
            values=["none",
                    "animals-pets",
                    "architecture",
                    "art-abstract",
                    "cars-vehicles",
                    "characters-creatures",
                    "cultural-heritage-history",
                    "electronics-gadgets",
                    "fashion-style",
                    "food-drink",
                    "furniture-home",
                    "music",
                    "nature-plants",
                    "news-politics",
                    "people",
                    "places-travel",
                    "science-technology",
                    "sports-fitness",
                    "weapons-military"],
        ),
        desc.BoolParam(
            name="isPublished",
            label="Publish",
            description="If the model is not published, it will be saved as a draft.",
            value=False,
        ),
        desc.BoolParam(
            name="isInspectable",
            label="Inspectable",
            description="Allow 2D view in model inspector.",
            value=True,
        ),
        desc.BoolParam(
            name="isPrivate",
            label="Private",
            description="Requires a pro account.",
            value=False,
        ),
        desc.StringParam(
            name="password",
            label="Password",
            description="Requires a pro account.",
            value="",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]
    
    def upload(self, apiToken, modelFile, data, chunk):
        modelEndpoint = 'https://api.sketchfab.com/v3/models'
        f = open(modelFile, 'rb')
        file = {'modelFile': (os.path.basename(modelFile), f.read())}
        file.update(data)
        f.close()
        (files, contentType) = requests.packages.urllib3.filepost.encode_multipart_formdata(file)
        headers = {'Authorization': 'Token {}'.format(apiToken), 'Content-Type': contentType}
        body = BufferReader(files, progressUpdate, cb_kwargs={'logManager': chunk.logManager}, stopped=self.stopped)
        chunk.logger.info('Uploading...')
        try:
            r = requests.post(
                modelEndpoint, **{'data': body, 'headers': headers})
            chunk.logManager.completeProgressBar()
        except requests.exceptions.RequestException as e:
            chunk.logger.error(u'An error occurred: {}'.format(e))
            raise RuntimeError() 
        if r.status_code != requests.codes.created:
            chunk.logger.error(u'Upload failed with error: {}'.format(r.json()))
            raise RuntimeError()

    def resolvedPaths(self, inputFiles):
        paths = []
        for inputFile in inputFiles:
            if os.path.isdir(inputFile.value):
                for path, subdirs, files in os.walk(inputFile.value):
                    for name in files:
                        paths.append(os.path.join(path, name))
            else:
                for f in glob.glob(inputFile.value):
                    paths.append(f)
        return paths

    def stopped(self):
        return self._stopped

    def processChunk(self, chunk):
        try:
            self._stopped = False
            chunk.logManager.start(chunk.node.verboseLevel.value)
            uploadFile = ''
        
            if not chunk.node.inputFiles:
                chunk.logger.warning('Nothing to upload')
                return
            if chunk.node.apiToken.value == '':
                chunk.logger.error('Need API token.')
                raise RuntimeError()
            if len(chunk.node.title.value) > 48:
                chunk.logger.error('Title cannot be longer than 48 characters.')
                raise RuntimeError()
            if len(chunk.node.description.value) > 1024:
                chunk.logger.error('Description cannot be longer than 1024 characters.')
                raise RuntimeError()
            tags = [ i.value.replace(' ', '-') for i in chunk.node.tags.value.values() ]
            if all(len(i) > 48 for i in tags) and len(tags) > 0:
                chunk.logger.error('Tags cannot be longer than 48 characters.')
                raise RuntimeError()
            if len(tags) > 42:
                chunk.logger.error('Maximum of 42 separate tags.')
                raise RuntimeError()

            data = {
                'name': chunk.node.title.value,
                'description': chunk.node.description.value,
                'license': chunk.node.license.value,
                'tags': str(tags),
                'isPublished': chunk.node.isPublished.value,
                'isInspectable': chunk.node.isInspectable.value,
                'private': chunk.node.isPrivate.value,
                'password': chunk.node.password.value
            }
            if chunk.node.category.value != 'none':
                data.update({'categories': chunk.node.category.value})
            chunk.logger.debug('Data to be sent: {}'.format(str(data)))
            
            # pack files into .zip to reduce file size and simplify process
            uploadFile = os.path.join(chunk.node.internalFolder, 'temp.zip')
            files = self.resolvedPaths(chunk.node.inputFiles.value)
            zf = zipfile.ZipFile(uploadFile, 'w')
            for file in files:
                zf.write(file, os.path.basename(file))
            zf.close()
            chunk.logger.debug('Files added to zip: {}'.format(str(files)))
            chunk.logger.debug('Created {}'.format(uploadFile))
            chunk.logger.info('File size: {}MB'.format(round(os.path.getsize(uploadFile)/(1024*1024), 3)))

            self.upload(chunk.node.apiToken.value, uploadFile, data, chunk)
            chunk.logger.info('Upload successful. Your model is being processed on Sketchfab. It may take some time to show up on your "models" page.')
        except Exception as e:
            chunk.logger.error(e)
            raise RuntimeError()
        finally:
            if os.path.isfile(uploadFile):
                os.remove(uploadFile)
                chunk.logger.debug('Deleted {}'.format(uploadFile))

            chunk.logManager.end()

    def stopProcess(self, chunk):
        self._stopped = True
