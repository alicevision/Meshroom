#!/usr/bin/env python

import logging
import os
from typing import List

from meshroom.core.mtyping import PathLike


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
