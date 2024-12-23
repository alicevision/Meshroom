#!/usr/bin/env python
# coding:utf-8
from PySide6.QtCore import QUrl, QFileInfo
from PySide6.QtCore import QObject, Slot

import os
import glob
import pyseq


class FilepathHelper(QObject):
    """
    FilepathHelper gives access to file path methods not available from JS.

    It should be non-instantiable and expose only static methods, but this is not yet
    possible in PySide.
    """

    @staticmethod
    def asStr(path):
        """
        Accepts strings and QUrls and always returns 'path' as a string.

        Args:
            path (str or QUrl): the filepath to consider

        Returns:
            str: String representation of 'path'
        """
        if not isinstance(path, (QUrl, str)):
            raise TypeError("Unexpected data type: {}".format(path.__class__))
        if isinstance(path, QUrl):
            path = path.toLocalFile()
        return path

    @Slot(str, result=str)
    @Slot(QUrl, result=str)
    def basename(self, path):
        """ Returns the final component of a pathname """
        return os.path.basename(self.asStr(path))

    @Slot(str, result=str)
    @Slot(QUrl, result=str)
    def dirname(self, path):
        """ Returns the directory component of a pathname """
        return os.path.dirname(self.asStr(path))

    @Slot(str, result=str)
    @Slot(QUrl, result=str)
    def extension(self, path):
        """ Returns the extension (.ext) of a pathname """
        return os.path.splitext(self.asStr(path))[-1]

    @Slot(str, result=str)
    @Slot(QUrl, result=str)
    def removeExtension(self, path):
        """ Returns the pathname without its extension (.ext)"""
        return os.path.splitext(self.asStr(path))[0]

    @Slot(str, result=bool)
    @Slot(QUrl, result=bool)
    def accessible(self, path):
        """ Returns whether a path is accessible for the user """
        path = self.asStr(path)
        return os.path.isdir(self.asStr(path)) and os.access(path, os.R_OK) and os.access(path, os.W_OK)

    @Slot(str, result=bool)
    @Slot(QUrl, result=bool)
    def isFile(self, path):
        """ Test whether a path is a regular file """
        return os.path.isfile(self.asStr(path))

    @Slot(str, result=bool)
    @Slot(QUrl, result=bool)
    def exists(self, path):
        """ Test whether a path exists """
        return os.path.exists(self.asStr(path))

    @Slot(QUrl, result=str)
    def urlToString(self, url):
        """ Convert QUrl to a string using 'QUrl.toLocalFile' method """
        return self.asStr(url)

    @Slot(str, result=QUrl)
    def stringToUrl(self, path):
        """ Convert a path (string) to a QUrl using 'QUrl.fromLocalFile' method """
        return QUrl.fromLocalFile(path)

    @Slot(str, result=str)
    @Slot(QUrl, result=str)
    def normpath(self, path):
        """ Returns native normalized path """
        return os.path.normpath(self.asStr(path))

    @Slot(str, result=str)
    @Slot(QUrl, result=str)
    def globFirst(self, path):
        """ Returns the first from a list of paths matching a pathname pattern. """
        import glob
        fileList = glob.glob(self.asStr(path))
        fileList.sort()
        if fileList:
          return fileList[0]
        return ""

    @Slot(QUrl, result=int)
    def fileSizeMB(self, path):
        """ Returns the file size in MB. """
        return QFileInfo(self.asStr(path)).size() / (1024*1024)

    @Slot(str, QObject, result=str)
    def resolve(self, path, vp):
        # Resolve dynamic path that depends on viewpoint

        replacements = {}
        if vp == None:
            replacements = FilepathHelper.getFilenamesFromFolder(FilepathHelper, FilepathHelper.dirname(FilepathHelper, path), FilepathHelper.extension(FilepathHelper, path))
            resolved = [path for i in range(len(replacements))]
            for key in replacements:
                for i in range(len(resolved)):
                    resolved[i] = resolved[i].replace("<FRAMEID>", replacements[i])
            return resolved
        else:

            vpPath = vp.childAttribute("path").value
            filename = FilepathHelper.basename(FilepathHelper, vpPath)
            replacements = {
                "<VIEW_ID>": str(vp.childAttribute("viewId").value),
                "<INTRINSIC_ID>": str(vp.childAttribute("intrinsicId").value),
                "<POSE_ID>": str(vp.childAttribute("poseId").value),
                "<PATH>": vpPath,
                "<FILENAME>": filename,
                "<FILESTEM>": FilepathHelper.removeExtension(FilepathHelper, filename),
                "<EXTENSION>": FilepathHelper.extension(FilepathHelper, filename),
            }

        resolved = path
        for key in replacements:
            resolved = resolved.replace(key, replacements[key])

        return resolved
    
    @Slot(str, result="QVariantList")
    @Slot(str, str, result="QVariantList")
    def getFilenamesFromFolder(self, folderPath: str, extension: str = None):
        """
        Get all filenames from a folder with a specific extension.

        :param folderPath: Path to the folder.
        :param extension: Extension of the files to get.
        :return: List of filenames.
        """
        if extension is None:
            extension = ".*"
        return [self.basename(f) for f in glob.glob(os.path.join(folderPath, f"*{extension}")) if os.path.isfile(f)]

    @Slot(str, bool, result="QVariantList")
    def resolveSequence(self, path, includesSeqMissingFiles):
        """
        Get id of each file in the sequence.
        """
        # use of pyseq to get the sequences
        seqs = pyseq.get_sequences(self.asStr(path))

        frameRanges = [[seq.start(), seq.end()] for seq in seqs]

        # create the resolved path for each sequence
        if includesSeqMissingFiles:
            resolved = []
            for seq in seqs:
                if not seq.frames():
                    # In case of a single frame, pyseq does not exctract a frameNumber
                    s = [fileItem.path for fileItem in seq]
                else:
                    # Create all frames between start and end, even for missing files
                    s = [seq.format("%D%h%p%t") % frameNumber for frameNumber in range(seq.start(), seq.end() + 1)]
                resolved.append(s)
        else:
            resolved = [[fileItem.path for fileItem in seq] for seq in seqs]
        return frameRanges, resolved
