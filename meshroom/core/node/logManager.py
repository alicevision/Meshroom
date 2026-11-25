#!/usr/bin/env python

import contextlib
import logging
import os
import sys
from typing import List

from meshroom.core.mtyping import PathLike


@contextlib.contextmanager
def redirectOutput(logFile: PathLike):
    """
    Append the standard output and error of the current process to 'logFile', as when a chunk is computed in its
    own process: both the Python ones (print) and the ones of native code (e.g. a DCC).
    """
    sys.stdout.flush()
    sys.stderr.flush()
    savedFds = (os.dup(1), os.dup(2))
    try:
        # Line buffered, so that the prints and the log records written to the same file stay in order
        with open(logFile, "a", buffering=1) as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            os.dup2(f.fileno(), 1)
            os.dup2(f.fileno(), 2)
            # shortcut: the C stdio buffers of native code are not flushed before the output is restored, so its
            # last lines can reach the console instead; flush them with ctypes if a DCC loses log lines
            yield
    finally:
        os.dup2(savedFds[0], 1)
        os.dup2(savedFds[1], 2)
        os.close(savedFds[0])
        os.close(savedFds[1])


class LogManager:
    dateTimeFormatting = '%H:%M:%S'

    def __init__(self, logger, logFile):
        self.logger: logging.Logger = logger
        self.logFile: PathLike = logFile
        self._previousHandlers: List[logging.Handler] = []
        self._previousLevel: int = 0

    class Formatter(logging.Formatter):
        def format(self, record):
            # Make level name lower case
            record.levelname = record.levelname.lower()
            return logging.Formatter.format(self, record)

    def configureLogger(self):
        self._previousLevel = self.logger.level
        self._previousHandlers = []
        for handler in self.logger.handlers[:]:
            self._previousHandlers.append(handler)
            self.logger.removeHandler(handler)
        handler = logging.FileHandler(self.logFile)
        formatter = self.Formatter('[%(asctime)s.%(msecs)03d][%(levelname)s] %(message)s',
                                   self.dateTimeFormatting)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def restorePreviousLogger(self):
        for h in self.logger.handlers[:]:
            self.logger.removeHandler(h)
        for h in self._previousHandlers:
            self.logger.addHandler(h)
        self.logger.setLevel(self._previousLevel)

    def clearLogFile(self):
        open(self.logFile, 'w').close()

    def start(self, level):
        # Make sure the log file exists
        if not os.path.exists(self.logFile):
            self.clearLogFile()
        self.configureLogger()
        self.logger.propagate = False
        self.logger.setLevel(self.textToLevel(level))
        self.progressBar = False

    def end(self):
        for handler in self.logger.handlers[:]:
            # Stops the file being locked
            handler.close()

    def makeProgressBar(self, end, message=''):
        assert end > 0
        assert not self.progressBar

        self.progressEnd = end
        self.currentProgressTics = 0
        self.progressBar = True

        with open(self.logFile, 'a') as f:
            if message:
                f.write(message+'\n')
            f.write('0%   10   20   30   40   50   60   70   80   90   100%\n')
            f.write('|----|----|----|----|----|----|----|----|----|----|\n\n')

            f.close()

        with open(self.logFile, "r") as f:
            content = f.read()
            self.progressBarPosition = content.rfind('\n')

    def updateProgressBar(self, value):
        assert self.progressBar
        assert value <= self.progressEnd

        tics = round((value/self.progressEnd)*51)

        with open(self.logFile, "r+") as f:
            text = f.read()
            for i in range(tics-self.currentProgressTics):
                text = text[:self.progressBarPosition]+'*'+text[self.progressBarPosition:]
            f.seek(0)
            f.write(text)

        self.currentProgressTics = tics

    def completeProgressBar(self):
        assert self.progressBar

        self.progressBar = False

    @staticmethod
    def textToLevel(text):
        text = text.lower()
        if text in ["critical", "fatal"]:
            return logging.CRITICAL
        elif text == "error":
            return logging.ERROR
        elif text == "warning":
            return logging.WARNING
        elif text == "info":
            return logging.INFO
        elif text == "debug":
            return logging.DEBUG
        elif text == "trace":
            return logging.TRACE
        else:
            return logging.NOTSET
