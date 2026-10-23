import operator


def _isCanonicalViewId(viewId):
    """ Return True if 'viewId' is the str() of an int, i.e. a key the lookup table can answer. """
    try:
        return str(int(viewId)) == viewId
    except (TypeError, ValueError):
        return False


def findViewpoint(viewpoints, viewId):
    """ Linear search of the first viewpoint whose viewId matches 'viewId' (as a str), None if not found. """
    return next((vp for vp in viewpoints if str(vp.viewId.value) == viewId), None)


class _Entry:
    """ Lookup table of a single viewpoints list, valid as long as the list content and the viewIds are unchanged. """

    def __init__(self, viewpoints, onViewIdChanged):
        self.viewpoints = viewpoints
        self._onViewIdChanged = onViewIdChanged
        self._snapshot = []
        self._viewIdAttrs = []
        self._table = None

    def matches(self, viewpoints):
        """ Return True if 'viewpoints' still holds the same viewpoints objects, in the same order, as the table. """
        return len(viewpoints) == len(self._snapshot) and all(map(operator.is_, viewpoints, self._snapshot))

    def invalidate(self):
        """ Drop the table and stop listening to the viewIds. """
        for attr in self._viewIdAttrs:
            try:
                attr.valueChanged.disconnect(self._onViewIdChanged)
                attr.inputLinksChanged.disconnect(self._onViewIdChanged)
            except RuntimeError:
                # The attribute has already been destroyed
                pass
        self._snapshot = []
        self._viewIdAttrs = []
        self._table = None

    def markDirty(self):
        """ Rebuild the table on next call to 'get'. """
        self._table = None

    def get(self, viewId):
        """ Return the viewpoint matching the canonical 'viewId', rebuilding the table if needed. """
        if self._table is None or not self.matches(self.viewpoints):
            self._build()
        if self._table is False:
            return findViewpoint(self._snapshot, viewId)
        return self._table.get(viewId)

    def _build(self):
        self.invalidate()
        self._snapshot = list(self.viewpoints)
        self._viewIdAttrs = [vp.viewId for vp in self._snapshot]
        for attr in self._viewIdAttrs:
            attr.valueChanged.connect(self._onViewIdChanged)
            attr.inputLinksChanged.connect(self._onViewIdChanged)
        table = {}
        for vp, attr in zip(self._snapshot, self._viewIdAttrs):
            value = attr.value
            if attr.isLink or (value is not None and type(value) is not int):
                # A linked viewId can change without notification and a non-int value does not
                # compare like its str() key: fall back to the linear search for this list
                table = False
                break
            if value is not None:
                # Keep the first match, like the linear search
                table.setdefault(str(value), vp)
        self._table = table


class ViewpointLookup:
    """
    Cached search of a viewpoint by viewId in viewpoints lists (e.g. CameraInit.viewpoints.value).

    'get' always returns the same viewpoint as findViewpoint(viewpoints, viewId):
      - a list is checked against a snapshot of its items on each call, so adding, removing or
        reordering viewpoints is detected whatever the order in which signals are delivered;
      - editing or linking a viewId drops the table and calls 'onInvalidated'.
    """

    # Number of viewpoints lists kept in cache (e.g. a CameraInit and a temporary CameraInit)
    MAX_LISTS = 4

    def __init__(self, onInvalidated=None):
        """
        Args:
            onInvalidated: callable invoked when a viewId has been edited, so callers that depend
                           on the lookup result can query it again.
        """
        self._entries = []  # most recently used last
        self._onInvalidated = onInvalidated

    def get(self, viewpoints, viewId):
        """
        Return the first viewpoint of 'viewpoints' whose viewId matches 'viewId', None if not found.

        Args:
            viewpoints: the list model of viewpoints to search in.
            viewId (str): the viewId to look for.
        """
        if viewpoints is None or len(viewpoints) == 0:
            return None
        if not _isCanonicalViewId(viewId):
            return findViewpoint(viewpoints, viewId)
        return self._entry(viewpoints).get(viewId)

    def clear(self):
        """ Drop all the tables. """
        for entry in self._entries:
            entry.invalidate()
        self._entries = []

    def _entry(self, viewpoints):
        for entry in self._entries:
            if entry.viewpoints is viewpoints:
                self._entries.remove(entry)
                self._entries.append(entry)
                return entry
        entry = _Entry(viewpoints, self._onViewIdChanged)
        self._entries.append(entry)
        if len(self._entries) > self.MAX_LISTS:
            self._entries.pop(0).invalidate()
        return entry

    def _onViewIdChanged(self):
        # Only mark tables as outdated: disconnecting here would modify the slots of the signal being emitted
        for entry in self._entries:
            entry.markDirty()
        if self._onInvalidated:
            self._onInvalidated()
