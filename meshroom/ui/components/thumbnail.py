from meshroom.common import Signal

from PySide6.QtCore import QObject, Slot, QSize, QUrl, QStandardPaths

from pyalicevision import image as avImage
import os
from pathlib import Path
import stat
import hashlib
import time
import logging
from threading import Thread
from multiprocessing.pool import ThreadPool


class ThumbnailCache(QObject):
    """
    ThumbnailCache provides an abstraction for the thumbnail cache on disk, available in QML.

    For a given image file, it ensures the corresponding thumbnail exists (by creating it if necessary)
    and gives access to it.
    Since creating thumbnails can be long (as it requires to read the full image from disk)
    it is performed asynchronously to avoid blocking the main thread.

    The default cache location can be overriden with the MESHROOM_THUMBNAIL_DIR environment variable.

    This class also takes care of cleaning the thumbnail directory,
    i.e. scanning this directory and removing thumbnails that have not been used for too long.
    This operation also ensures that the number of thumbnails on disk does not exceed a certain limit,
    by removing thumbnails if necessary (from least recently used to most recently used).
    Since this operation is done at application startup, it is also performed asynchronously.

    The default time limit is 90 days,
    and can be overriden with the MESHROOM_THUMBNAIL_TIME_LIMIT environment variable.

    The default maximum number of thumbnails on disk is 100000,
    and can be overriden with the MESHROOM_MAX_THUMBNAILS_ON_DISK.

    The main use case for thumbnails in Meshroom is in the ImageGallery.
    """

    # Thumbnail cache directory
    # Cannot be initialized here as it depends on the organization and application names
    thumbnailDir: str = ''

    # Thumbnail dimensions limit (the actual dimensions of a thumbnail will depend on the aspect ratio)
    thumbnailSize: QSize = QSize(256, 256)

    # Time limit for thumbnail storage on disk, expressed in days
    storageTimeLimit: int = 90

    # Maximum number of thumbnails in the cache directory
    maxThumbnailsOnDisk: int = 100000

    # Signal to notify listeners that a thumbnail was created and written on disk
    # This signal has two argument:
    # - the url of the image that the thumbnail is associated to
    # - an identifier for the caller, e.g. the component that sent the request (useful for faster dispatch in QML)
    thumbnailCreated = Signal(QUrl, int)

    # Threads info and LIFO structure for running clean and createThumbnail asynchronously
    requests = []
    cleaningThread = None
    workerThreads = ThreadPool(processes=3)

    def __del__(self):
        self.workerThreads.terminate()
        self.workerThreads.join()

    @staticmethod
    def initialize():
        """ Initialize static fields in cache class and cache directory on disk. """
        # Thumbnail directory: default or user specified
        dir = os.getenv('MESHROOM_THUMBNAIL_DIR')
        if dir is not None:
            ThumbnailCache.thumbnailDir = dir
        else:
            ThumbnailCache.thumbnailDir = os.path.join(QStandardPaths.writableLocation(QStandardPaths.CacheLocation),
                                                       'thumbnails')

        # User specifed time limit for thumbnails on disk (expressed in days)
        timeLimit = os.getenv('MESHROOM_THUMBNAIL_TIME_LIMIT')
        if timeLimit is not None:
            ThumbnailCache.storageTimeLimit = float(timeLimit)

        # User specifed maximum number of thumbnails on disk
        maxOnDisk = os.getenv('MESHROOM_MAX_THUMBNAILS_ON_DISK')
        if maxOnDisk is not None:
            ThumbnailCache.maxThumbnailsOnDisk = int(maxOnDisk)

        # Clean thumbnail directory
        # This is performed asynchronously to avoid freezing the app at startup
        ThumbnailCache.cleaningThread = Thread(target=ThumbnailCache.clean)
        ThumbnailCache.cleaningThread.start()

        # Make sure the thumbnail directory exists before writing into it
        try:
            os.makedirs(ThumbnailCache.thumbnailDir, exist_ok=True)
        except OSError:
            logging.warning(f'[ThumbnailCache] Failed to create directory: {ThumbnailCache.thumbnailDir}')
            pass

    @staticmethod
    def clean():
        """
        Scan the thumbnail directory and:
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
        for f_name in os.listdir(ThumbnailCache.thumbnailDir):
            pathname = os.path.join(ThumbnailCache.thumbnailDir, f_name)

            # System call to get current item info
            f_stat = os.stat(pathname, follow_symlinks=False)

            # Check if this is a regular file
            if not stat.S_ISREG(f_stat.st_mode):
                continue

            # Compute storage duration since last usage of thumbnail
            lastUsage = f_stat.st_mtime
            storageTime = now - lastUsage
            # logging.debug(f'[ThumbnailCache] Thumbnail {f_name} has been stored for {storageTime}s')

            if storageTime > ThumbnailCache.storageTimeLimit * 3600 * 24:
                # Mark as removable if storage time exceeds limit
                logging.debug(f'[ThumbnailCache] {f_name} exceeded storage time limit')
                toRemove.append(pathname)
            else:
                # Store path and last usage time for potentially sorting and removing later
                remaining.append((pathname, lastUsage))

        # Remove all thumbnails marked as removable
        for path in toRemove:
            logging.debug(f'[ThumbnailCache] Remove {path}')
            try:
                os.remove(path)
            except FileNotFoundError:
                logging.error(f'[ThumbnailCache] Tried to remove {path} but this file does not exist')

        # Check if number of thumbnails on disk exceeds limit
        if len(remaining) > ThumbnailCache.maxThumbnailsOnDisk:
            nbToRemove = len(remaining) - ThumbnailCache.maxThumbnailsOnDisk
            logging.debug(
                f'[ThumbnailCache] Too many thumbnails: {len(remaining)} remaining, {nbToRemove} will be removed')

            # Sort by last usage order and remove excess
            remaining.sort(key=lambda elt: elt[1])
            for i in range(nbToRemove):
                path = remaining[i][0]
                logging.debug(f'[ThumbnailCache] Remove {path}')
                try:
                    os.remove(path)
                except FileNotFoundError:
                    logging.error(f'[ThumbnailCache] Tried to remove {path} but this file does not exist')

    @staticmethod
    def thumbnailPath(imgPath: str) -> str:
        """
        Use SHA1 hashing to associate a unique thumbnail to an image.

        Args:
            imgPath: filepath to the input image

        Returns:
            The filepath to the corresponding thumbnail
        """
        digest = hashlib.sha1(imgPath.encode('utf-8')).hexdigest()
        path = os.path.join(ThumbnailCache.thumbnailDir, f'{digest}.jpg')
        return path

    @staticmethod
    def removeOutdated(imgPath: str, path: str):
        """
        Remove thumbnail if its corresponding image has been modified after thumbnail creation.

        Args:
            imgPath: filepath to the input image
            path: filepath to the corresponding thumbnail
        """
        try:
            if os.path.getmtime(imgPath) > os.path.getmtime(path):
                os.remove(path)
        except OSError:
            return
        except FileNotFoundError:
            return

    @staticmethod
    def checkThumbnail(path: str) -> bool:
        """
        Check if a thumbnail already exists on disk, and if so update its last modification time.

        Args:
            path: filepath to the thumbnail

        Returns:
            Whether the thumbnail exists on disk or not
        """
        if os.path.exists(path):
            # Update last modification time
            Path(path).touch(exist_ok=True)
            return True
        return False

    @Slot(QUrl, int, result=QUrl)
    def thumbnail(self, imgSource: QUrl, callerID: int) -> QUrl | None:
        """
        Retrieve the filepath of the thumbnail corresponding to a given image.

        If the thumbnail does not exist on disk, it will be created asynchronously.
        When this is done, the thumbnailCreated signal is emitted.

        Args:
            imgSource: location of the input image
            callerID: identifier for the object that requested the thumbnail

        Returns:
            The location of the corresponding thumbnail if it exists, otherwise None
        """
        if not imgSource.isValid():
            return None

        if not os.path.exists(ThumbnailCache.thumbnailDir):
            return imgSource

        imgPath = imgSource.toLocalFile()
        path = ThumbnailCache.thumbnailPath(imgPath)

        # Remove thumbnail in case it is outdated (i.e. if image was modified)
        ThumbnailCache.removeOutdated(imgPath, path)

        # Check if thumbnail already exists (and update its last modification time)
        if ThumbnailCache.checkThumbnail(path):
            source = QUrl.fromLocalFile(path)
            return source

        # Thumbnail does not exist
        # Create request and submit to worker threads
        ThumbnailCache.requests.append((imgSource, callerID))
        ThumbnailCache.workerThreads.apply_async(func=self.handleRequestsAsync)

        return None

    @staticmethod
    def _createEmptyThumbnail(path: str):
        """ Create an empty thumbnail file on disk. """
        try:
            with open(path, 'a') as f:
                os.utime(path, None)
        except Exception as exc:
            logging.error(f'[ThumbnailCache] Failed to create empty thumbnail at {path}: {exc}')

    def createThumbnail(self, imgSource: QUrl, callerID: int) -> str:
        """
        Load an image, resize it to thumbnail dimensions and save the result in the cache directory.

        Args:
            imgSource: location of the input image
            callerID: identifier for the object that requested the thumbnail

        Returns:
            The filepath of the created thumbnail, which may be an empty file if an error happened during the process
        """
        imgPath = imgSource.toLocalFile()
        path = ThumbnailCache.thumbnailPath(imgPath)

        # Check if thumbnail already exists (it may have been created by another thread)
        if ThumbnailCache.checkThumbnail(path):
            self.thumbnailCreated.emit(imgSource, callerID)
            return path

        logging.debug(f'[ThumbnailCache] Creating thumbnail {path} for image {imgPath}')

        # Read image with pyalicevision (uses OpenImageIO, supports RAW, EXR, and other formats)
        image = avImage.Image_RGBColor()
        readOptions = avImage.ImageReadOptions(avImage.EImageColorSpace_SRGB)
        try:
            avImage.readImage(imgPath, image, readOptions)
        except Exception as exc:
            logging.error(f'[ThumbnailCache] Error when reading image: {exc}')
            logging.error(f'[ThumbnailCache] Creating empty thumbnail for {imgPath}')
            ThumbnailCache._createEmptyThumbnail(path)
            self.thumbnailCreated.emit(imgSource, callerID)
            return path

        # Compute thumbnail dimensions preserving aspect ratio
        w, h = image.width(), image.height()

        if w == 0 or h == 0:
            logging.error(f'[ThumbnailCache] Error when reading image: null image')
            logging.error(f'[ThumbnailCache] Creating empty thumbnail for {imgPath}')
            ThumbnailCache._createEmptyThumbnail(path)
            self.thumbnailCreated.emit(imgSource, callerID)
            return path

        maxW, maxH = ThumbnailCache.thumbnailSize.width(), ThumbnailCache.thumbnailSize.height()
        scale = min(maxW / w, maxH / h)
        newW = max(1, round(w * scale))
        newH = max(1, round(h * scale))

        # Downscale image using pyalicevision (uses OpenImageIO high-quality resampling)
        thumbnail = avImage.Image_RGBColor()
        avImage.resizeImage(newW, newH, image, thumbnail)

        # Write thumbnail with pyalicevision
        writeOptions = avImage.ImageWriteOptions()
        # Data is already in sRGB; skip any color-space conversion during write.
        writeOptions.toColorSpace(avImage.EImageColorSpace_NO_CONVERSION)
        try:
            avImage.writeImage(path, thumbnail, writeOptions, avImage.oiioParams().get())
        except Exception as exc:
            logging.error(f'[ThumbnailCache] Error when writing thumbnail: {exc}')
            logging.error(f'[ThumbnailCache] Creating empty thumbnail for {imgPath}')
            ThumbnailCache._createEmptyThumbnail(path)

        # Notify listeners
        self.thumbnailCreated.emit(imgSource, callerID)
        return path

    def handleRequestsAsync(self):
        """
        Process thumbnail creation requests in LIFO order.

        Note: this operation waits for the cleaning process to finish before starting,
        in order to avoid synchronization issues.
        """
        # Wait for cleaning thread to finish
        if ThumbnailCache.cleaningThread is not None and ThumbnailCache.cleaningThread.is_alive():
            ThumbnailCache.cleaningThread.join()

        # Handle requests until the requests stack is empty
        try:
            while True:
                req = ThumbnailCache.requests.pop()
                self.createThumbnail(req[0], req[1])
        except IndexError:
            # No more request to process
            return

    @Slot()
    def clearRequests(self):
        """
        Clear all pending thumbnail creation requests.

        Requests already under treatment by a worker thread will still be completed.
        """
        ThumbnailCache.requests.clear()
