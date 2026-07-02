from meshroom.common import Property, Signal

class Collapsable(object):

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

    def _restoreCollapseState(self, serializedValue):
        if isinstance(serializedValue, dict) and "expanded" in serializedValue:
            self.expanded = serializedValue["expanded"]

    expandedChanged = Signal()
    isCollapsable = Property(bool, lambda self: True, constant=True)
    expanded = Property(bool, _getExpanded, _setExpanded, notify=expandedChanged)
