"""
Layout of the dockable panels of the Meshroom UI.

The layout is a JSON-serializable tree describing where each panel is displayed. This module has no
Qt dependency so that its logic can be unit tested; `meshroom.ui.dockLayoutManager` exposes it to QML
and persists it in the application settings.

Nodes:
- a "tabs" node is a group of panels displayed as tabs, one of them being the current one:
    {"type": "tabs", "id": "node4", "panels": ["graphEditor", "taskManager"], "current": "graphEditor"}
- a "split" node displays its children side by side, "sizes" holding the fraction of the available
  space given to each of them:
    {"type": "split", "id": "node1", "orientation": "horizontal", "sizes": [0.6, 0.4], "children": [...]}

Layout:
    {
        "version": 1,
        "main": <node or None>,     # content of the main window
        "floating": [               # floating windows
            {"id": "node9", "geometry": [x, y, width, height] or None, "root": <node>},
        ],
        "closed": ["textViewer"],   # panels currently closed
    }

Every known panel appears exactly once in the tree, closed ones included: closing a panel keeps its
place, so that it is reopened where it was.
"""

import copy
import math

LAYOUT_VERSION = 1

HORIZONTAL = "horizontal"
VERTICAL = "vertical"

# Drop zones on a tabs node: "center" adds the panel to its tabs, the other ones split the node.
ZONES = ("center", "left", "right", "top", "bottom")

# Panels that cannot be displayed in a floating window: the Qt3D scene of the 3D Viewer does not
# survive a change of window.
NON_FLOATABLE_PANELS = ("viewer3D",)

# Layout of the Meshroom main window by default: the viewers above, the graph and the node editors below.
DEFAULT_LAYOUT = {
    "version": LAYOUT_VERSION,
    "main": {
        "type": "split",
        "orientation": VERTICAL,
        "sizes": [0.55, 0.45],
        "children": [
            {
                "type": "split",
                "orientation": HORIZONTAL,
                "sizes": [0.27, 0.28, 0.45],
                "children": [
                    {"type": "tabs", "panels": ["imageGallery"]},
                    {"type": "tabs", "panels": ["imageViewer", "textViewer"]},
                    {"type": "tabs", "panels": ["viewer3D"]},
                ],
            },
            {
                "type": "split",
                "orientation": HORIZONTAL,
                "sizes": [0.6, 0.4],
                "children": [
                    {"type": "tabs", "panels": ["graphEditor", "taskManager", "scriptEditor"]},
                    {"type": "tabs", "panels": ["nodeEditor"]},
                ],
            },
        ],
    },
    "closed": ["textViewer"],
}


def _isPositiveNumber(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _cleanGeometry(geometry):
    """ Return a valid [x, y, width, height] geometry as integers, or None. """
    if not isinstance(geometry, (list, tuple)) or len(geometry) != 4:
        return None
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in geometry):
        return None
    if geometry[2] <= 0 or geometry[3] <= 0:
        return None
    return [int(v) for v in geometry]


def clampGeometry(geometry, screens):
    """
    Fit a window geometry in the screen it overlaps the most, moving and shrinking it if needed. A window
    overlapping no screen, e.g. saved while another screen was connected, goes to the first screen.

    Args:
        geometry: [x, y, width, height] of the window, or None.
        screens: [x, y, width, height] of the available area of each screen.

    Returns:
        list: the fitted geometry, or the given one if there is no geometry or no screen.
    """
    if not geometry or not screens:
        return geometry
    x, y, width, height = geometry

    def overlap(screen):
        sx, sy, sw, sh = screen
        return max(0, min(x + width, sx + sw) - max(x, sx)) * max(0, min(y + height, sy + sh) - max(y, sy))

    # The first screen wins when the window overlaps none
    sx, sy, sw, sh = max(screens, key=overlap)
    width, height = min(width, sw), min(height, sh)
    return [min(max(x, sx), sx + sw - width), min(max(y, sy), sy + sh - height), width, height]


def iterNodes(node):
    """
    Iterate over a node and all its descendants, depth first.

    Yields:
        (node, parent) tuples, parent being None for the given node.
    """
    stack = [(node, None)]
    while stack:
        current, parent = stack.pop()
        if current is None:
            continue
        yield current, parent
        if current["type"] == "split":
            stack.extend((child, current) for child in reversed(current["children"]))


def panelsOf(node):
    """ Return the ids of the panels found in a node and its descendants, in display order. """
    panels = []
    for current, _ in iterNodes(node):
        if current["type"] == "tabs":
            panels.extend(current["panels"])
    return panels


class DockLayout:
    """
    A dock layout, kept normalized after each change:
    - each known panel appears exactly once, unknown ones are dropped,
    - there is no empty tabs node and no split node with less than two children,
    - a split node has no child split with the same orientation (it is merged into its parent),
    - the sizes of a split node are positive fractions summing to 1,
    - every node has a unique id.
    """

    def __init__(self, defaultLayout=DEFAULT_LAYOUT, nonFloatablePanels=NON_FLOATABLE_PANELS):
        """
        Args:
            defaultLayout: the layout used by `reset`, which also defines the known panels.
            nonFloatablePanels: ids of the panels that cannot be displayed in a floating window.
        """
        self._nextId = 1
        self._panelIds = panelsOf(defaultLayout["main"])
        for window in defaultLayout.get("floating", []):
            self._panelIds += panelsOf(window["root"])
        self._nonFloatable = set(nonFloatablePanels)
        self._default = copy.deepcopy(defaultLayout)
        self._layout = None
        self.reset()

    @property
    def panelIds(self):
        """ The ids of the known panels. """
        return list(self._panelIds)

    def toDict(self):
        """ Return a copy of the layout, suitable for JSON serialization. """
        return copy.deepcopy(self._layout)

    def reset(self):
        """ Restore the default layout. """
        self._layout = self._normalized(copy.deepcopy(self._default))

    def load(self, data):
        """
        Load a layout, typically deserialized from the settings.
        Unknown panels are dropped and missing ones are added back to the group they belong to by default.

        Returns:
            bool: whether the data was a valid layout; if not, the current layout is left unchanged.
        """
        if not isinstance(data, dict) or data.get("version") != LAYOUT_VERSION:
            return False
        self._layout = self._normalized(copy.deepcopy(data))
        return True

    # --- Queries ----------------------------------------------------------------------------------

    def isOpen(self, panelId):
        return panelId in self._panelIds and panelId not in self._layout["closed"]

    def openPanels(self):
        """ Return the ids of the open panels. """
        return [panelId for panelId in self._panelIds if self.isOpen(panelId)]

    def node(self, nodeId):
        """ Return the node with the given id, or None. """
        return self._find(lambda node: node.get("id") == nodeId)[0]

    def groupOf(self, panelId):
        """ Return the tabs node containing the given panel, or None. """
        return self._findGroup(panelId)[0]

    def canFloat(self, panelId):
        return panelId in self._panelIds and panelId not in self._nonFloatable

    def floatingWindow(self, windowId):
        """ Return the floating window with the given id, or None. """
        return next((entry for entry in self._layout["floating"] if entry["id"] == windowId), None)

    # --- Changes ----------------------------------------------------------------------------------

    def setPanelOpen(self, panelId, isOpen):
        """
        Open or close a panel. It stays at its place in the tree either way.

        Returns:
            bool: whether the layout changed.
        """
        if panelId not in self._panelIds or self.isOpen(panelId) == isOpen:
            return False
        if isOpen:
            self._layout["closed"].remove(panelId)
        else:
            self._layout["closed"].append(panelId)
        return True

    def setCurrent(self, groupId, panelId):
        """
        Make a panel the current tab of its group.

        Returns:
            bool: whether the layout changed.
        """
        group = self.node(groupId)
        if not group or group["type"] != "tabs" or panelId not in group["panels"] or group["current"] == panelId:
            return False
        group["current"] = panelId
        return True

    def setSizes(self, splitId, sizes):
        """
        Update the sizes of the children of a split node, typically after the user dragged a handle.

        Args:
            splitId: the id of the split node.
            sizes: the new size of each child (in any unit), or a negative value for the children that
                are not displayed (their panels are all closed): those keep their current fraction, the
                displayed ones share the rest proportionally to the given sizes.

        Returns:
            list: the new sizes (fractions) of the node, or None if the sizes could not be applied.
        """
        split = self.node(splitId)
        if not split or split["type"] != "split" or len(sizes) != len(split["sizes"]):
            return None
        shown = [i for i, size in enumerate(sizes) if _isPositiveNumber(size)]
        if not shown:
            return None
        available = sum(split["sizes"][i] for i in shown)
        total = sum(sizes[i] for i in shown)
        for i in shown:
            split["sizes"][i] = available * sizes[i] / total
        return list(split["sizes"])

    def movePanel(self, panelId, groupId, zone, index=-1):
        """
        Move a panel next to a tabs node, as a user would by dragging its tab. The moved panel is
        opened and made current.

        Args:
            panelId: the panel to move.
            groupId: the id of the target tabs node.
            zone: "center" to add the panel to the tabs of the target, "left", "right", "top" or
                "bottom" to split the target and put the panel on that side.
            index: for the "center" zone, the position of the new tab among the tabs of the target
                (as they are before the move); -1 appends it.

        Returns:
            bool: whether the layout changed.
        """
        source = self.groupOf(panelId)
        target, _, targetWindow = self._find(lambda node: node.get("id") == groupId)
        if zone not in ZONES or not source or not target or target["type"] != "tabs":
            return False
        if targetWindow and not self.canFloat(panelId):
            return False

        if zone == "center":
            panels = target["panels"]
            index = len(panels) if index < 0 else min(index, len(panels))
            if target is source:
                # Reorder the tabs of the group
                oldIndex = panels.index(panelId)
                if index > oldIndex:
                    index -= 1
                if index == oldIndex and target["current"] == panelId and self.isOpen(panelId):
                    return False
                panels.remove(panelId)
            else:
                source["panels"].remove(panelId)
            panels.insert(index, panelId)
            target["current"] = panelId
        else:
            if target is source and len(source["panels"]) == 1:
                # Splitting a group with itself
                return False
            source["panels"].remove(panelId)
            self._insertBeside(target, self._newTabs([panelId]), zone)

        self.setPanelOpen(panelId, True)
        self._layout = self._normalized(self._layout)
        return True

    def floatPanel(self, panelId, geometry=None):
        """
        Move a panel to a new floating window. The panel is opened.

        Args:
            panelId: the panel to move.
            geometry: [x, y, width, height] of the window, or None to let the UI decide.

        Returns:
            str: the id of the new floating window, or None if the panel cannot float or is already
            alone in a floating window.
        """
        source, _, window = self._findGroup(panelId)
        if not source or not self.canFloat(panelId):
            return None
        if window and panelsOf(window["root"]) == [panelId]:
            return None
        source["panels"].remove(panelId)
        windowId = self._newId()
        self._layout["floating"].append({
            "id": windowId,
            "geometry": _cleanGeometry(geometry),
            "root": self._newTabs([panelId]),
        })
        self.setPanelOpen(panelId, True)
        self._layout = self._normalized(self._layout)
        return windowId

    def dockPanel(self, panelId):
        """
        Move a panel from a floating window back to the main window, in the group of the panels it is
        grouped with by default. The panel is opened and made current.

        Returns:
            bool: whether the layout changed.
        """
        source, _, window = self._findGroup(panelId)
        if not window:
            return False
        source["panels"].remove(panelId)
        self._insertHome(panelId)
        self.groupOf(panelId)["current"] = panelId
        self.setPanelOpen(panelId, True)
        self._layout = self._normalized(self._layout)
        return True

    def setFloatingGeometry(self, windowId, geometry):
        """
        Store the geometry of a floating window, as moved or resized by the user.

        Returns:
            bool: whether the layout changed.
        """
        window = self.floatingWindow(windowId)
        geometry = _cleanGeometry(geometry)
        if not window or not geometry or window["geometry"] == geometry:
            return False
        window["geometry"] = geometry
        return True

    def closeFloatingWindow(self, windowId):
        """
        Close the panels of a floating window. The window keeps its place in the layout, to be displayed
        again at the same place when one of its panels is reopened.

        Returns:
            bool: whether the layout changed.
        """
        window = self.floatingWindow(windowId)
        if not window:
            return False
        changed = [self.setPanelOpen(panelId, False) for panelId in panelsOf(window["root"])]
        return any(changed)

    def clampFloatingGeometries(self, screens):
        """ Fit each floating window in the given screens (see `clampGeometry`). """
        for window in self._layout["floating"]:
            window["geometry"] = clampGeometry(window["geometry"], screens)

    # --- Internals --------------------------------------------------------------------------------

    def _iterAllNodes(self):
        """
        Iterate over the nodes of the main window and of the floating windows, depth first.

        Yields:
            (node, parent, window) tuples, window being the floating window containing the node, or
            None in the main window.
        """
        for node, parent in iterNodes(self._layout["main"]):
            yield node, parent, None
        for window in self._layout["floating"]:
            for node, parent in iterNodes(window["root"]):
                yield node, parent, window

    def _find(self, predicate):
        """ Return the (node, parent, window) tuple of the first node matching predicate, or Nones. """
        return next((entry for entry in self._iterAllNodes() if predicate(entry[0])), (None, None, None))

    def _findGroup(self, panelId):
        """ Return the (node, parent, window) tuple of the tabs node containing a panel, or Nones. """
        return self._find(lambda node: node["type"] == "tabs" and panelId in node["panels"])

    def _newId(self):
        nodeId = f"node{self._nextId}"
        self._nextId += 1
        return nodeId

    def _newTabs(self, panels):
        return {"type": "tabs", "id": self._newId(), "panels": panels, "current": panels[0]}

    def _insertBeside(self, target, node, zone):
        """ Insert `node` on the `zone` side of `target`, splitting it or reusing its parent split. """
        orientation = HORIZONTAL if zone in ("left", "right") else VERTICAL
        after = zone in ("right", "bottom")
        _, parent, window = self._find(lambda node: node is target)
        # Node ids are unique: equality finds the target itself
        i = parent["children"].index(target) if parent else None

        if parent and parent["orientation"] == orientation:
            # The parent already lays its children out in that direction: share the space of the target
            half = parent["sizes"][i] / 2
            parent["sizes"][i] = half
            j = i + 1 if after else i
            parent["children"].insert(j, node)
            parent["sizes"].insert(j, half)
            return

        split = {
            "type": "split",
            "id": self._newId(),
            "orientation": orientation,
            "sizes": [0.5, 0.5],
            "children": [target, node] if after else [node, target],
        }
        if parent:
            parent["children"][i] = split
        elif window:
            window["root"] = split
        else:
            self._layout["main"] = split

    def _normalized(self, data):
        """ Return a normalized copy of a layout (see the class documentation). """
        seen = set()
        layout = {
            "version": LAYOUT_VERSION,
            "main": self._cleanNode(data.get("main"), seen),
            "floating": [],
            "closed": [],
        }
        windows = data.get("floating")
        for window in windows if isinstance(windows, list) else []:
            if not isinstance(window, dict):
                continue
            # Non floatable panels found in a floating window go back to their default place
            root = self._cleanNode(window.get("root"), seen, excluded=self._nonFloatable)
            if root is not None:
                geometry = _cleanGeometry(window.get("geometry"))
                layout["floating"].append({"id": window.get("id"), "geometry": geometry, "root": root})
        closed = data.get("closed")
        closed = closed if isinstance(closed, list) else []
        for panelId in closed:
            if panelId in self._panelIds and panelId not in layout["closed"]:
                layout["closed"].append(panelId)
        self._layout = layout
        # Before adding the missing panels, which may create nodes with new ids
        self._assignIds()

        # Panels missing from the tree, e.g. added in a newer version, go back to their default place
        for panelId in self._panelIds:
            if panelId not in seen:
                self._insertHome(panelId)
                if panelId in self._default.get("closed", []) and panelId not in closed:
                    layout["closed"].append(panelId)

        return layout

    def _cleanNode(self, node, seen, excluded=()):
        """
        Return a normalized copy of a node, or None if nothing is left of it.

        Args:
            node: the node to clean up.
            seen: the ids of the panels already found in the layout, updated with the ones of the node.
            excluded: ids of panels that must be dropped from this node.
        """
        if not isinstance(node, dict):
            return None
        if node.get("type") == "tabs":
            return self._cleanTabs(node, seen, excluded)
        if node.get("type") == "split":
            return self._cleanSplit(node, seen, excluded)
        return None

    def _cleanTabs(self, node, seen, excluded):
        panels = []
        for panelId in node.get("panels") or []:
            if panelId in self._panelIds and panelId not in seen and panelId not in excluded:
                seen.add(panelId)
                panels.append(panelId)
        if not panels:
            return None
        current = node.get("current")
        return {
            "type": "tabs",
            "id": node.get("id"),
            "panels": panels,
            "current": current if current in panels else panels[0],
        }

    def _cleanSplit(self, node, seen, excluded):
        orientation = node.get("orientation")
        orientation = orientation if orientation in (HORIZONTAL, VERTICAL) else HORIZONTAL
        children = node.get("children")
        children = children if isinstance(children, list) else []
        sizes = node.get("sizes")
        if not isinstance(sizes, list) or len(sizes) != len(children) or not all(_isPositiveNumber(s) for s in sizes):
            sizes = [1.0] * len(children)

        kept = []
        for child, size in zip(children, sizes):
            child = self._cleanNode(child, seen, excluded)
            if child is None:
                continue
            if child["type"] == "split" and child["orientation"] == orientation:
                # Merge a split with the same orientation into this one
                kept.extend((grandChild, size * s) for grandChild, s in zip(child["children"], child["sizes"]))
            else:
                kept.append((child, size))

        if not kept:
            return None
        if len(kept) == 1:
            return kept[0][0]
        total = sum(size for _, size in kept)
        return {
            "type": "split",
            "id": node.get("id"),
            "orientation": orientation,
            "sizes": [size / total for _, size in kept],
            "children": [child for child, _ in kept],
        }

    def _insertHome(self, panelId):
        """
        Add a panel missing from the layout to the group it belongs to by default: the first group
        containing one of the panels it is grouped with in the default layout, else the first group.
        """
        homeGroup = next((n for n, _ in iterNodes(self._default["main"])
                          if n["type"] == "tabs" and panelId in n["panels"]), None)
        siblings = [p for p in homeGroup["panels"] if p != panelId] if homeGroup else []
        groups = [n for n, _ in iterNodes(self._layout["main"]) if n["type"] == "tabs"]
        group = next((g for g in groups if any(p in g["panels"] for p in siblings)), None)
        group = group or (groups[0] if groups else None)
        if group:
            group["panels"].append(panelId)
        else:
            self._layout["main"] = self._newTabs([panelId])

    def _assignIds(self):
        """
        Give an id to the nodes and floating windows without one, or with an id already used. The ids
        generated from now on never collide with the "nodeN" ids kept.
        """
        items = self._layout["floating"] + [node for node, _, _ in self._iterAllNodes()]
        for item in items:
            nodeId = item.get("id")
            if isinstance(nodeId, str) and nodeId.startswith("node") and nodeId[4:].isdecimal():
                self._nextId = max(self._nextId, int(nodeId[4:]) + 1)
        used = set()
        for item in items:
            nodeId = item.get("id")
            if not isinstance(nodeId, str) or not nodeId or nodeId in used:
                item["id"] = nodeId = self._newId()
            used.add(nodeId)


# Panel visibility settings of the versions of Meshroom without docking ("UILayout" settings category),
# with the panels they applied to.
LEGACY_VISIBILITY_SETTINGS = {
    "showImageGallery": ["imageGallery"],
    "showImageViewer": ["imageViewer"],
    "showTextViewer": ["textViewer"],
    "showViewer3D": ["viewer3D"],
    # The Graph Editor checkbox used to hide the whole bottom part of the window
    "showGraphEditor": ["graphEditor", "taskManager", "scriptEditor", "nodeEditor"],
}


def applyLegacySettings(dockLayout, settings):
    """
    Apply the panel visibility settings of the versions of Meshroom without docking to a layout.

    Args:
        dockLayout (DockLayout): the layout to update, typically the default one.
        settings (dict): the values of the legacy settings found, by key; booleans may be stored as
            "true"/"false" strings.
    """
    for key, panelIds in LEGACY_VISIBILITY_SETTINGS.items():
        value = settings.get(key)
        if value is None:
            continue
        isOpen = value.lower() == "true" if isinstance(value, str) else bool(value)
        for panelId in panelIds:
            dockLayout.setPanelOpen(panelId, isOpen)
