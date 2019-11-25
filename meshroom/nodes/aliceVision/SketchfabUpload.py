__version__ = "1.0"

from meshroom.core import desc
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
                 cb_kwargs={}):
        self._callback = callback
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs
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
        return chunk

def progressUpdate(size=None, progress=None, logManager=None):
    if not logManager.progressBar:
        logManager.makeProgressBar(size, 'Upload progress:')

    logManager.updateProgressBar(progress)

class SketchfabUpload(desc.Node):
    size = desc.DynamicNodeSize('inputFiles')
    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="input",
                label="Input",
                description="",
                value="",
                uid=[0],
            ),
            name="inputFiles",
            label="Input Files",
            description="Input Files to export.",
            group="",
        ),
        desc.ChoiceParam(
            name='maxSize',
            label='Maximum Upload Size',
            description='The maximum upload size in MB.',
            value=50,
            values=(50, 200, 500),
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='limitSize',
            label='Limit Upload Size',
            description='Change maximum download size in advanced attributes.',
            value=True,
            uid=[0],
        ),
        desc.StringParam(
            name='apiToken',
            label='API Token',
            description='Get your token from https://sketchfab.com/settings/password',
            value='',
            uid=[0],
        ),
        desc.StringParam(
            name='title',
            label='Title',
            description='Title cannot be longer than 48 characters.',
            value='',
            uid=[0],
        ),
        desc.StringParam(
            name='description',
            label='Description',
            description='Description cannot be longer than 1024 characters.',
            value='',
            uid=[0],
        ),
        desc.StringParam(
            name='license',
            label='License',
            description='License label.',
            value='CC Attribution',
            uid=[0],
        ),
        desc.BoolParam(
            name='isPublished',
            label='Publish',
            description='If the model is not published it will be saved as a draft.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='isInspectable',
            label='Inspectable',
            description='Allow 2D view in model inspector.',
            value=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (critical, error, warning, info, debug).''',
            value='info',
            values=['critical', 'error', 'warning', 'info', 'debug'],
            exclusive=True,
            uid=[],
        ),
    ]

    def resolvedPaths(self, inputFiles):
        paths = []
        for inputFile in inputFiles:
            for f in glob.glob(inputFile.value):
                paths.append(f)
        return paths
    
    def upload(self, apiToken, modelFile, data, chunk):
        modelEndpoint = 'https://api.sketchfab.com/v3/models'
        f = open(modelFile, 'rb')
        file = {'modelFile': (os.path.basename(modelFile), f.read()), **data}
        (files, contentType) = requests.packages.urllib3.filepost.encode_multipart_formdata(file)
        headers = {'Authorization': 'Token {}'.format(apiToken), 'Content-Type': contentType}
        body = BufferReader(files, progressUpdate, cb_kwargs={'logManager': chunk.logManager})
        chunk.logger.info('Uploading...')
        try:
            r = requests.post(
                modelEndpoint, **{'data': body, 'headers': headers})
            f.close()
            chunk.logManager.completeProgressBar()
        except requests.exceptions.RequestException as e:
            f.close()
            chunk.logger.error(u'An error occured: {}'.format(e))
            raise RuntimeError() 
        if r.status_code != requests.codes.created:
            chunk.logger.error(u'Upload failed with error: {}'.format(r.json()))
            raise RuntimeError()

    def processChunk(self, chunk):
        chunk.logManager.waitUntilCleared()
        chunk.logger.setLevel(chunk.logManager.textToLevel(chunk.node.verboseLevel.value))
        
        if not chunk.node.inputFiles:
            chunk.logger.warning('Nothing to upload')
            return
        if len(chunk.node.title.value) > 48:
            chunk.logger.error('Title cannot be longer than 48 characters.')
            raise RuntimeError()
        if len(chunk.node.description.value) > 1024:
            chunk.logger.error('Description cannot be longer than 1024 characters.')
            raise RuntimeError()
        if chunk.node.apiToken.value == '':
            chunk.logger.error('Need API token.')
            raise RuntimeError()
        data = {
            'name': chunk.node.title.value,
            'description': chunk.node.description.value,
            'license': chunk.node.license.value,
            'isPublished': chunk.node.isPublished.value,
            'isInspectable': chunk.node.isInspectable.value
        }
        # pack files into .zip to reduce file size and simplify process
        uploadFile = os.path.join(chunk.node.internalFolder, 'temp.zip')
        files = self.resolvedPaths(chunk.node.inputFiles.value)
        zf = zipfile.ZipFile(uploadFile, 'w')
        for file in files:
            zf.write(file, os.path.basename(file))
        zf.close()
        chunk.logger.info('Successfully created {}'.format(uploadFile))
        
        fileSize = os.path.getsize(uploadFile)/1000000
        chunk.logger.info('File size: {}MB'.format(fileSize))
        if chunk.node.limitSize.value and fileSize > chunk.node.maxSize.value:
            chunk.logger.error('File too big.')
            raise RuntimeError()
        
        self.upload(chunk.node.apiToken.value, uploadFile, data, chunk)
        chunk.logger.info('Upload successful. Your model is being processed on Sketchfab. It may take some time to show up on your "models" page.')
