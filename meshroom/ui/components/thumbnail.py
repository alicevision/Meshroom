from meshroom.common import Signal

from PySide2.QtCore import QObject, Slot, QSize, QUrl, Qt
from PySide2.QtGui import QImageReader, QImageWriter

import os
from pathlib import Path
import hashlib
import time
import logging
from multiprocessing.pool import ThreadPool


class ThumbnailCache(QObject):
    """ThumbnailCache provides an abstraction for the thumbnail cache on disk, available in QML.

    For a given image file, it ensures the corresponding thumbnail exists (by creating it if necessary)
    and gives access to it.
    Since creating thumbnails can be long (as it requires to read the full image from disk)
    it is performed asynchronously to avoid blocking the main thread.

    The default cache location is a subdirectory of the user's home directory:
    ~/Meshroom/thumbnails.
    This location can be overriden with the MESHROOM_THUMBNAIL_DIR environment variable.

    This class also takes care of cleaning the thumbnail directory,
    i.e. scanning this directory and removing thumbnails that have not been used for too long.
    This operation also ensures that the number of thumbnails on disk does not exceed a certain limit, 
    by removing thumbnails if necessary (from least recently used to most recently used).

    The default time limit is 90 days, 
    and can be overriden with the MESHROOM_THUMBNAIL_TIME_LIMIT environment variable.

    The default maximum number of thumbnails on disk is 100000, 
    and can be overriden with the MESHROOM_MAX_THUMBNAILS_ON_DISK.

    The main use case for thumbnails in Meshroom is in the ImageGallery.
    """

    # Thumbnail cache directory
    thumbnailDir = os.path.join(Path.home(), 'Meshroom', 'thumbnails')

    # Thumbnail dimensions limit (the actual dimensions of a thumbnail will depend on the aspect ratio)
    thumbnailSize = QSize(100, 100)

    # Time limit for thumbnail storage on disk, expressed in days
    storageTimeLimit = 90

    # Maximum number of thumbnails in the cache directory
    maxThumbnailsOnDisk = 100000

    # Signal to notify listeners that a thumbnail was created and written on disk
    # This signal has one argument: the url of the image that the thumbnail is associated to
    thumbnailCreated = Signal(QUrl)

    # Thread pool for running createThumbnail asynchronously on a fixed number of worker threads
    pool = ThreadPool()

    @staticmethod
    def initialize():
        """Initialize static fields in cache class and cache directory on disk."""
        # User specified thumbnail directory
        dir = os.getenv('MESHROOM_THUMBNAIL_DIR')
        if dir is not None:
            ThumbnailCache.thumbnailDir = dir

        # User specifed time limit for thumbnails on disk (expressed in days)
        timeLimit = os.getenv('MESHROOM_THUMBNAIL_TIME_LIMIT')
        if timeLimit is not None:
            ThumbnailCache.storageTimeLimit = float(timeLimit)

        # User specifed maximum number of thumbnails on disk
        maxOnDisk = os.getenv('MESHROOM_MAX_THUMBNAILS_ON_DISK')
        if maxOnDisk is not None:
            ThumbnailCache.maxThumbnailsOnDisk = int(maxOnDisk)

        # Clean thumbnail directory
        ThumbnailCache.clean()

        # Make sure the thumbnail directory exists before writing into it
        os.makedirs(ThumbnailCache.thumbnailDir, exist_ok=True)

    @staticmethod
    def thumbnailPath(imgPath):
        """Use SHA1 hashing to associate a unique thumbnail to an image.

        Args:
            imgPath (str): filepath to the input image

        Returns:
            str: filepath to the corresponding thumbnail
        """
        digest = hashlib.sha1(imgPath.encode('utf-8')).hexdigest()
        path = os.path.join(ThumbnailCache.thumbnailDir, f'{digest}.jpg')
        return path

    @Slot(QUrl, result=QUrl)
    def thumbnail(self, imgSource):
        """Retrieve the filepath of the thumbnail corresponding to a given image.

        If the thumbnail does not exist on disk, it will be created asynchronously.
        When this is done, the createdThumbnail signal is emitted.

        Args:
            imgSource (QUrl): location of the input image

        Returns:
            QUrl: location of the corresponding thumbnail if it exists, otherwise None
        """
        if not imgSource.isValid():
            return None

        imgPath = imgSource.toLocalFile()
        path = ThumbnailCache.thumbnailPath(imgPath)
        source = QUrl.fromLocalFile(path)

        # Check if thumbnail already exists
        if os.path.exists(path):
            # Update last modification time
            Path(path).touch(exist_ok=True)
            return source

        # Thumbnail does not exist
        # create it in a worker thread to avoid UI freeze
        ThumbnailCache.pool.apply_async(self.createThumbnail, args=(imgSource,))
        return None

    def createThumbnail(self, imgSource):
        """Load an image, resize it to thumbnail dimensions and save the result in the cache directory.

        Args:
            imgSource (QUrl): location of the input image
        """
        imgPath = imgSource.toLocalFile()
        path = ThumbnailCache.thumbnailPath(imgPath)
        logging.debug(f'[ThumbnailCache] Creating thumbnail {path} for image {imgPath}')

        # Initialize image reader object
        reader = QImageReader()
        reader.setFileName(imgPath)
        reader.setAutoTransform(True)

        # Read image and check for potential errors
        img = reader.read()
        if img.isNull():
            logging.error(f'[ThumbnailCache] Error when reading image: {reader.errorString()}')
            return

        # Scale image while preserving aspect ratio
        thumbnail = img.scaled(ThumbnailCache.thumbnailSize, aspectMode=Qt.KeepAspectRatio)

        # Write thumbnail to disk and check for potential errors
        writer = QImageWriter(path)
        success = writer.write(thumbnail)
        if not success:
            logging.error(f'[ThumbnailCache] Error when writing thumbnail: {writer.errorString()}')

        # Notify listeners
        self.thumbnailCreated.emit(imgSource)

    @staticmethod
    def clean():
        """Scan the thumbnail directory and:
        1. remove all thumbnails that have not been used for more than storageTimeLimit days
        2. ensure that the number of thumbnails on disk does not exceed maxThumbnailsOnDisk.
        """
        # Check if thumbnail directory exists
        if not os.path.exists(ThumbnailCache.thumbnailDir):
            logging.debug('[ThumbnailCache] Thumbnail directory does not exist yet.')
            return

        # Get current time
        now = time.time()

        # Scan thumbnail directory and gather all thumbnails to remove
        toRemove = []
        remaining = []
        for entry in os.scandir(ThumbnailCache.thumbnailDir):
            if not entry.is_file():
                continue

            # Compute storage duration since last usage of thumbnail
            lastUsage = os.path.getmtime(entry.path)
            storageTime = now - lastUsage
            logging.debug(f'[ThumbnailCache] Thumbnail {entry.name} has been stored for {storageTime}s')

            if storageTime > ThumbnailCache.storageTimeLimit * 3600 * 24:
                # Mark as removable if storage time exceeds limit
                logging.debug(f'[ThumbnailCache] {entry.name} exceeded storage time limit')
                toRemove.append(entry.path)
            else:
                # Store path and last usage time for potentially sorting and removing later
                remaining.append((entry.path, lastUsage))

        # Remove all thumbnails marked as removable
        for path in toRemove:
            logging.debug(f'[ThumbnailCache] Remove {path}')
            os.remove(path)

        # Check if number of thumbnails on disk exceeds limit
        if len(remaining) > ThumbnailCache.maxThumbnailsOnDisk:
            nbToRemove = len(remaining) - ThumbnailCache.maxThumbnailsOnDisk
            logging.debug(f'[ThumbnailCache] Too many thumbnails: {len(remaining)} remaining, {nbToRemove} will be removed')

            # Sort by last usage order and remove excess
            remaining.sort(key=lambda elt: elt[1])
            for i in range(nbToRemove):
                path = remaining[i][0]
                logging.debug(f'[ThumbnailCache] Remove {path}')
                os.remove(path)
