#!/usr/bin/env python
# coding:utf-8
from meshroom.core import pyCompatibility

from PySide2.QtCore import QUrl
from PySide2.QtCore import QObject, Slot

import os


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
        if not isinstance(path, (QUrl, pyCompatibility.basestring)):
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
