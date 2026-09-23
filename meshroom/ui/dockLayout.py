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

    def __init__(self, defaultLayout=DEFAULT_LAYOUT):
        """
        Args:
            defaultLayout: the layout used by `reset`, which also defines the known panels.
        """
        self._nextId = 1
        self._panelIds = panelsOf(defaultLayout["main"])
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
        data = copy.deepcopy(data)
        self._reserveIds(data)
        self._layout = self._normalized(data)
        return True

    # --- Queries ----------------------------------------------------------------------------------

    def isOpen(self, panelId):
        return panelId in self._panelIds and panelId not in self._layout["closed"]

    def openPanels(self):
        """ Return the ids of the open panels. """
        return [panelId for panelId in self._panelIds if self.isOpen(panelId)]

    def node(self, nodeId):
        """ Return the node with the given id, or None. """
        for root in self._roots():
            for node, _ in iterNodes(root):
                if node.get("id") == nodeId:
                    return node
        return None

    def groupOf(self, panelId):
        """ Return the tabs node containing the given panel, or None. """
        for root in self._roots():
            for node, _ in iterNodes(root):
                if node["type"] == "tabs" and panelId in node["panels"]:
                    return node
        return None

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
        target = self.node(groupId)
        if zone not in ZONES or not source or not target or target["type"] != "tabs":
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

    # --- Internals --------------------------------------------------------------------------------

    def _roots(self):
        return [self._layout["main"]]

    def _newId(self):
        nodeId = f"node{self._nextId}"
        self._nextId += 1
        return nodeId

    def _newTabs(self, panels):
        return {"type": "tabs", "id": self._newId(), "panels": panels, "current": panels[0]}

    def _reserveIds(self, data):
        """ Make sure the ids generated from now on do not collide with the "nodeN" ids found in `data`. """
        def ids(value):
            if isinstance(value, dict):
                yield value.get("id")
                for child in value.values():
                    yield from ids(child)
            elif isinstance(value, list):
                for child in value:
                    yield from ids(child)

        for nodeId in ids(data):
            if isinstance(nodeId, str) and nodeId.startswith("node") and nodeId[4:].isdigit():
                self._nextId = max(self._nextId, int(nodeId[4:]) + 1)

    def _setRoot(self, oldRoot, newRoot):
        """ Replace a root node of the layout. """
        self._layout["main"] = newRoot

    def _insertBeside(self, target, node, zone):
        """ Insert `node` on the `zone` side of `target`, splitting it or reusing its parent split. """
        orientation = HORIZONTAL if zone in ("left", "right") else VERTICAL
        after = zone in ("right", "bottom")
        parent = next((p for n, p in self._iterAllNodes() if n is target), None)

        if parent and parent["orientation"] == orientation:
            # The parent already lays its children out in that direction: share the space of the target
            i = next(i for i, child in enumerate(parent["children"]) if child is target)
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
            i = next(i for i, child in enumerate(parent["children"]) if child is target)
            parent["children"][i] = split
        else:
            self._setRoot(target, split)

    def _iterAllNodes(self):
        for root in self._roots():
            yield from iterNodes(root)

    def _normalized(self, data):
        """ Return a normalized copy of a layout (see the class documentation). """
        seen = set()
        layout = {
            "version": LAYOUT_VERSION,
            "main": self._cleanNode(data.get("main"), seen),
            "closed": [],
        }
        closed = data.get("closed")
        closed = closed if isinstance(closed, list) else []
        for panelId in closed:
            if panelId in self._panelIds and panelId not in layout["closed"]:
                layout["closed"].append(panelId)
        self._layout = layout

        # Panels missing from the tree, e.g. added in a newer version, go back to their default place
        for panelId in self._panelIds:
            if panelId not in seen:
                self._insertHome(panelId)
                if panelId in self._default.get("closed", []) and panelId not in closed:
                    layout["closed"].append(panelId)

        self._assignIds()
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
        """ Give an id to the nodes without one, or with an id already used by another node. """
        used = set()
        for node, _ in self._iterAllNodes():
            nodeId = node.get("id")
            if not isinstance(nodeId, str) or not nodeId or nodeId in used:
                nodeId = self._newId()
                while nodeId in used:
                    nodeId = self._newId()
                node["id"] = nodeId
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
