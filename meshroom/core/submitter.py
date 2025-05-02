#!/usr/bin/env python

from meshroom.common import BaseObject, Property


class BaseSubmitter(BaseObject):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self._name = name

    def submit(self, nodes, edges, filepath, submitLabel="{projectName}"):
        """ Submit the given graph
         Returns:
             bool: whether the submission succeeded
        """
        raise NotImplementedError("'submit' method must be implemented in subclasses")

    name = Property(str, lambda self: self._name, constant=True)
