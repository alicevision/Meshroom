from PySide2.QtCore import QObject, Slot, QSize, QUrl, Qt
from PySide2.QtGui import QImageReader, QImageWriter

import hashlib
import pathlib
import os


class ThumbnailCache(QObject):
    """
    ThumbnailCache provides an abstraction for the thumbnail cache on disk, available in QML.

    For a given image file, it ensures the corresponding thumbnail exists (by creating it if necessary)
    and gives access to it.

    The default cache location is a subdirectory of the user's home directory:
    ~/Meshroom/thumbnails.
    This location can be overriden with the MESHROOM_THUMBNAIL_DIR environment variable.

    The main use case for thumbnails in Meshroom is in the ImageGallery.
    """

    thumbnailDir = os.path.join(pathlib.Path.home(), 'Meshroom', 'thumbnails')
    thumbnailSize = QSize(100, 100)

    @Slot(QUrl, result=QUrl)
    def thumbnail(self, imgSource):
        """
        Retrieve the filepath of the thumbnail corresponding to a given image.
        If the thumbnail does not exist on disk, it is created.

        Args:
            imgSource (QUrl): the filepath to the input image

        Returns:
            QUrl: the filepath to the corresponding thumbnail
        """
        # Safety check
        if not imgSource.isValid():
            return None

        imgPath = imgSource.toLocalFile()

        # Use SHA1 hashing to associate a unique thumbnail to the image
        digest = hashlib.sha1(imgPath.encode('utf-8')).hexdigest()
        path = os.path.join(ThumbnailCache.thumbnailDir, f'{digest}.jpg')
        source = QUrl.fromLocalFile(path)

        # Check if thumbnail already exists
        if os.path.exists(path):
            return source

        # Thumbnail does not exist, therefore we create it:
        # 1. read the image
        # 2. scale it to thumbnail dimensions
        # 3. write it in the cache
        print(f'[ThumbnailCache] Creating thumbnail {path} for image {imgPath}')

        # Initialize image reader object
        reader = QImageReader()
        reader.setFileName(imgPath)
        reader.setAutoTransform(True)

        # Read image and check for potential errors
        img = reader.read()
        if img.isNull():
            print(f'[ThumbnailCache] Error when reading image: {reader.errorString()}')
            return None

        # Make sure the thumbnail directory exists before writing into it
        os.makedirs(ThumbnailCache.thumbnailDir, exist_ok=True)

        # Scale image while preserving aspect ratio
        thumbnail = img.scaled(ThumbnailCache.thumbnailSize, aspectMode=Qt.KeepAspectRatio)

        # Write thumbnail to disk and check for potential errors
        writer = QImageWriter(path)
        success = writer.write(thumbnail)
        if not success:
            print(f'[ThumbnailCache] Error when writing thumbnail: {writer.errorString()}')
            return None

        return source
