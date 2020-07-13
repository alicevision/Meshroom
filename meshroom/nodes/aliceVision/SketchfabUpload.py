__version__ = "1.0"

import glob
import os
import json
import zipfile
import requests
import io
import time

from meshroom.core import desc, stats


class BufferReader(io.BytesIO): # object to call the callback while the file is being uploaded
    def __init__(self, buf=b'',
                 callback=None,
                 logManager=None,
                 stopped=None):
        self._callback = callback
        self._logManager = logManager
        self._stopped = stopped
        self._progress = 0
        self._len = len(buf)
        io.BytesIO.__init__(self, buf)

    def __len__(self):
        return self._len

    def read(self, n=-1):
        if self._stopped():
            raise RuntimeError('Node stopped by user')
        chunk = io.BytesIO.read(self, n)
        self._progress += int(len(chunk))
        if self._callback:
            try:
                self._callback(self._len, self._progress, self._logManager)
            except Exception as e: # catches exception from the callback so the upload does not stop
                self._logManager.logger.warning('Error at callback: {}'.format(e))
        return chunk

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
        desc.BoolParam(
            name='includeMeshroomFiles',
            label='Include Meshroom Files',
            description='Include "log", "statistics" and "status" in the .zip file that is uploaded.',
            value=False,
            uid=[0],
            advanced=True,
        ),
        desc.StringParam(
            name='apiToken',
            label='API Token',
            description='Get your token from https://sketchfab.com/settings/password.',
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
        desc.ChoiceParam(
            name='license',
            label='License',
            description='License label.',
            value='CC Attribution',
            values=['CC Attribution',
                    'CC Attribution-ShareAlike',
                    'CC Attribution-NoDerivs',
                    'CC Attribution-NonCommercial',
                    'CC Attribution-NonCommercial-ShareAlike',
                    'CC Attribution-NonCommercial-NoDerivs'],
            exclusive=True,
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.StringParam(
                name='tag',
                label='Tag',
                description='Tag cannot be longer than 48 characters.',
                value='',
                uid=[0],
            ),
            name="tags",
            label="Tags",
            description="Maximum of 42 separate tags.",
            group="",
        ),
        desc.ChoiceParam(
            name='category',
            label='Category',
            description='Adding categories helps improve the discoverability of your model.',
            value='none',
            values=['none',
                    'animals-pets',
                    'architecture',
                    'art-abstract',
                    'cars-vehicles',
                    'characters-creatures',
                    'cultural-heritage-history',
                    'electronics-gadgets',
                    'fashion-style',
                    'food-drink',
                    'furniture-home',
                    'music',
                    'nature-plants',
                    'news-politics',
                    'people',
                    'places-travel',
                    'science-technology',
                    'sports-fitness',
                    'weapons-military'],
            exclusive=True,
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
        desc.BoolParam(
            name='isPrivate',
            label='Private',
            description='Requires a pro account.',
            value=False,
            uid=[0],
        ),
        desc.StringParam(
            name='password',
            label='Password',
            description='Requires a pro account.',
            value='',
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

    def upload(self, apiToken, modelFile, data, chunk):
        modelEndpoint = 'https://api.sketchfab.com/v3/models'
        f = open(modelFile, 'rb')
        file = {'modelFile': (os.path.basename(modelFile), f.read())}
        file.update(data)
        f.close()
        (files, contentType) = requests.packages.urllib3.filepost.encode_multipart_formdata(file)
        headers = {'Authorization': 'Token {}'.format(apiToken), 'Content-Type': contentType}
        body = BufferReader(files, self.uploadCallback, chunk.logManager, self.stopped)
        chunk.logger.info('Uploading...')
        try:
            r = requests.post(
                modelEndpoint, **{'data': body, 'headers': headers})
            chunk.logManager.completeProgressBar()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(u'An error occured: {}'.format(e)) 
        if r.status_code != requests.codes.created:
            raise RuntimeError(u'Upload failed with error: {}'.format(r.json()))

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
            self._startTime = time.time()
            self._progressMeasuredAt = self._startTime
            self._progress = 0
            uploadFile = ''

            if not chunk.node.inputFiles:
                chunk.logger.warning('Nothing to upload')
                return
            if chunk.node.apiToken.value == '':
                raise RuntimeError('Need API token.')
            if len(chunk.node.title.value) > 48:
                raise RuntimeError('Title cannot be longer than 48 characters.')
            if len(chunk.node.description.value) > 1024:
                raise RuntimeError('Description cannot be longer than 1024 characters.')
            tags = [ i.value.replace(' ', '-') for i in chunk.node.tags.value.values() ]
            if all(len(i) > 48 for i in tags) and len(tags) > 0:
                raise RuntimeError('Tags cannot be longer than 48 characters.')
            if len(tags) > 42:
                raise RuntimeError('Maximum of 42 separate tags.')

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
            chunk.logger.debug('Data to be sent: '+str(data))

            # pack files into .zip to reduce file size and simplify process
            uploadFile = os.path.join(chunk.node.internalFolder,
                'Meshroom_{}.zip'.format("".join(x for x in chunk.node.title.value if x.isalnum()))) # use title in the file name for clarity, removing any non-alphanumeric characters
            files = self.resolvedPaths(chunk.node.inputFiles.value)
            chunk.logger.debug('Files to write: '+str(files))
            zf = zipfile.ZipFile(uploadFile, 'w')
            for file in files:
                if os.path.basename(file) in ('log', 'statistics', 'status') and not chunk.node.includeMeshroomFiles.value:
                    chunk.logger.debug('File skipped: '+file)
                else:
                    zf.write(file, os.path.basename(file))
            zf.close()
            chunk.logger.debug('Created file: '+uploadFile)
            chunk.logger.info('File size: '+stats.bytes2human(os.path.getsize(uploadFile)))

            self.upload(chunk.node.apiToken.value, uploadFile, data, chunk)
            chunk.logger.info('Upload successful. Your model is being processed on Sketchfab. It may take some time to show up on your "models" page.')
        except Exception as e:
            chunk.logger.error(e)
            raise e
        finally:
            if os.path.isfile(uploadFile):
                os.remove(uploadFile)
                chunk.logger.debug('Deleted file: '+uploadFile)

            chunk.logManager.end()

    def uploadCallback(self, size, progress, logManager):
        if not logManager.progressBar:
            logManager.makeProgressBar(size, 'Upload progress:')
        logManager.updateProgressBar(progress)

        self._progressMeasuredAt = time.time()
        if progress <= 0: # prevent division by 0
            progress = 1
        self._progress = size / progress

    def getEstimatedTime(self, chunk, reconstruction):
        if chunk.statusName == 'RUNNING':
            return self._progress * (self._progressMeasuredAt - self._startTime)
        return 0

    def stopProcess(self, chunk):
        self._stopped = True
