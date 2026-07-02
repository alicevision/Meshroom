from meshroom.common import Property, Signal

class Expandable(object):

    def __init__(self):
        super().__init__()

    def _getExpanded(self) -> bool:
        return getattr(self, "_expanded", False)

    def _setExpanded(self, value: bool):
        value = bool(value)
        if self._getExpanded() == value:
            return
        self._expanded = value
        self.expandedChanged.emit()

    def _restoreExpandedState(self, serializedValue):
        if isinstance(serializedValue, dict) and "expanded" in serializedValue:
            self.expanded = serializedValue["expanded"]

    expandedChanged = Signal()
    isExpandable = Property(bool, lambda self: True, constant=True)
    expanded = Property(bool, _getExpanded, _setExpanded, notify=expandedChanged)
