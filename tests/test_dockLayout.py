import json

from meshroom.ui.dockLayout import DockLayout, DEFAULT_LAYOUT, LAYOUT_VERSION, HORIZONTAL, VERTICAL, \
    applyLegacySettings, iterNodes, panelsOf


PANELS = ["a", "b", "c", "d"]


def smallLayout():
    """ A layout with two groups side by side: [a, b] | [c, d]. """
    return {
        "version": LAYOUT_VERSION,
        "main": {
            "type": "split",
            "orientation": HORIZONTAL,
            "sizes": [0.5, 0.5],
            "children": [
                {"type": "tabs", "panels": ["a", "b"]},
                {"type": "tabs", "panels": ["c", "d"]},
            ],
        },
        "closed": [],
    }


def groups(layout):
    """ Return the panels of each tabs node of the main window, in display order. """
    return [node["panels"] for node, _ in iterNodes(layout.toDict()["main"]) if node["type"] == "tabs"]


def checkNormalized(layout):
    data = layout.toDict()
    assert sorted(panelsOf(data["main"])) == sorted(layout.panelIds)
    ids = [node["id"] for node, _ in iterNodes(data["main"])]
    assert len(ids) == len(set(ids))
    for node, parent in iterNodes(data["main"]):
        if node["type"] == "split":
            assert len(node["children"]) >= 2
            assert abs(sum(node["sizes"]) - 1) < 1e-9
            assert all(child["type"] != "split" or child["orientation"] != node["orientation"] for child in node["children"])
        else:
            assert node["panels"] and node["current"] in node["panels"]


class TestDefaultLayout:

    def test_defaultLayoutContainsEveryPanelOnce(self):
        layout = DockLayout()
        checkNormalized(layout)
        assert layout.panelIds == ["imageGallery", "imageViewer", "textViewer", "viewer3D",
                                   "graphEditor", "taskManager", "scriptEditor", "nodeEditor"]

    def test_textViewerIsClosedByDefault(self):
        layout = DockLayout()
        assert not layout.isOpen("textViewer")
        assert "textViewer" not in layout.openPanels()
        assert layout.isOpen("graphEditor")

    def test_defaultLayoutIsNotModified(self):
        before = json.dumps(DEFAULT_LAYOUT, sort_keys=True)
        layout = DockLayout()
        layout.movePanel("nodeEditor", layout.groupOf("imageGallery")["id"], "center")
        layout.reset()
        assert json.dumps(DEFAULT_LAYOUT, sort_keys=True) == before
        assert layout.groupOf("nodeEditor")["panels"] == ["nodeEditor"]


class TestMovePanel:

    def test_moveToTheCenterOfAnotherGroupAddsATab(self):
        layout = DockLayout(smallLayout())
        assert layout.movePanel("a", layout.groupOf("c")["id"], "center")
        assert groups(layout) == [["b"], ["c", "d", "a"]]
        assert layout.groupOf("a")["current"] == "a"
        checkNormalized(layout)

    def test_moveAtATabIndex(self):
        layout = DockLayout(smallLayout())
        assert layout.movePanel("a", layout.groupOf("c")["id"], "center", 1)
        assert groups(layout) == [["b"], ["c", "a", "d"]]

    def test_emptiedGroupIsRemovedAndSplitCollapsed(self):
        layout = DockLayout(smallLayout())
        layout.movePanel("a", layout.groupOf("c")["id"], "center")
        layout.movePanel("b", layout.groupOf("c")["id"], "center")
        main = layout.toDict()["main"]
        assert main["type"] == "tabs"
        assert main["panels"] == ["c", "d", "a", "b"]
        checkNormalized(layout)

    def test_reorderTabsOfAGroup(self):
        layout = DockLayout(smallLayout())
        groupId = layout.groupOf("a")["id"]
        assert layout.movePanel("a", groupId, "center", 2)
        assert groups(layout) == [["b", "a"], ["c", "d"]]
        # Dropping a tab where it already is only makes it current
        assert layout.movePanel("b", groupId, "center", 0)
        assert not layout.movePanel("b", groupId, "center", 0)
        assert not layout.movePanel("b", groupId, "center", 1)

    def test_moveToAnEdgeSplitsTheTarget(self):
        layout = DockLayout(smallLayout())
        assert layout.movePanel("a", layout.groupOf("c")["id"], "bottom")
        main = layout.toDict()["main"]
        assert main["orientation"] == HORIZONTAL
        right = main["children"][1]
        assert right["type"] == "split" and right["orientation"] == VERTICAL
        assert [child["panels"] for child in right["children"]] == [["c", "d"], ["a"]]
        assert right["sizes"] == [0.5, 0.5]
        checkNormalized(layout)

    def test_moveToAnEdgeAlongTheParentSplitSharesTheTargetSpace(self):
        layout = DockLayout(smallLayout())
        assert layout.movePanel("d", layout.groupOf("c")["id"], "left")
        main = layout.toDict()["main"]
        assert [child["panels"] for child in main["children"]] == [["a", "b"], ["d"], ["c"]]
        assert main["sizes"] == [0.5, 0.25, 0.25]
        checkNormalized(layout)

    def test_splitOwnGroup(self):
        layout = DockLayout(smallLayout())
        assert layout.movePanel("b", layout.groupOf("a")["id"], "top")
        main = layout.toDict()["main"]
        left = main["children"][0]
        assert left["orientation"] == VERTICAL
        assert [child["panels"] for child in left["children"]] == [["b"], ["a"]]

    def test_cannotSplitAGroupWithItsOnlyPanel(self):
        layout = DockLayout(smallLayout())
        layout.movePanel("b", layout.groupOf("c")["id"], "center")
        before = layout.toDict()
        assert not layout.movePanel("a", layout.groupOf("a")["id"], "right")
        assert not layout.movePanel("a", layout.groupOf("a")["id"], "center")
        assert layout.toDict() == before

    def test_invalidMoves(self):
        layout = DockLayout(smallLayout())
        before = layout.toDict()
        splitId = layout.toDict()["main"]["id"]
        assert not layout.movePanel("unknown", layout.groupOf("c")["id"], "center")
        assert not layout.movePanel("a", "unknownGroup", "center")
        assert not layout.movePanel("a", splitId, "center")
        assert not layout.movePanel("a", layout.groupOf("c")["id"], "diagonal")
        assert layout.toDict() == before

    def test_movedPanelIsOpened(self):
        layout = DockLayout(smallLayout())
        layout.setPanelOpen("a", False)
        layout.movePanel("a", layout.groupOf("c")["id"], "right")
        assert layout.isOpen("a")

    def test_idsStayUniqueAcrossMoves(self):
        layout = DockLayout()
        for panelId, target, zone in [("taskManager", "graphEditor", "right"), ("scriptEditor", "taskManager", "bottom"),
                                      ("imageGallery", "nodeEditor", "top"), ("viewer3D", "scriptEditor", "center"),
                                      ("taskManager", "imageViewer", "left"), ("scriptEditor", "graphEditor", "center")]:
            assert layout.movePanel(panelId, layout.groupOf(target)["id"], zone)
            checkNormalized(layout)


class TestState:

    def test_openAndClosePanels(self):
        layout = DockLayout(smallLayout())
        assert layout.setPanelOpen("b", False)
        assert not layout.setPanelOpen("b", False)
        assert layout.openPanels() == ["a", "c", "d"]
        # A closed panel keeps its place
        assert groups(layout) == [["a", "b"], ["c", "d"]]
        assert layout.setPanelOpen("b", True)
        assert not layout.setPanelOpen("unknown", True)

    def test_setCurrent(self):
        layout = DockLayout(smallLayout())
        groupId = layout.groupOf("c")["id"]
        assert layout.setCurrent(groupId, "d")
        assert not layout.setCurrent(groupId, "d")
        assert not layout.setCurrent(groupId, "a")
        assert layout.groupOf("d")["current"] == "d"

    def test_setSizes(self):
        layout = DockLayout(smallLayout())
        layout.movePanel("d", layout.groupOf("c")["id"], "right")
        splitId = layout.toDict()["main"]["id"]
        assert layout.setSizes(splitId, [100, 300, 100]) == [0.2, 0.6, 0.2]
        # The children which are not displayed keep their fraction
        assert layout.setSizes(splitId, [-1, 100, 300]) == [0.2, 0.2, 0.6]
        assert layout.setSizes(splitId, [1, 2]) is None
        assert layout.setSizes(splitId, [-1, -1, -1]) is None
        assert layout.setSizes(layout.groupOf("a")["id"], [1]) is None


class TestLoad:

    def test_jsonRoundTrip(self):
        layout = DockLayout()
        layout.movePanel("taskManager", layout.groupOf("graphEditor")["id"], "right")
        layout.setPanelOpen("viewer3D", False)
        data = json.loads(json.dumps(layout.toDict()))
        other = DockLayout()
        assert other.load(data)
        assert other.toDict() == layout.toDict()

    def test_invalidDataIsRejected(self):
        layout = DockLayout(smallLayout())
        before = layout.toDict()
        assert not layout.load(None)
        assert not layout.load([])
        assert not layout.load({"version": LAYOUT_VERSION + 1, "main": None})
        assert layout.toDict() == before

    def test_unknownDuplicatedAndMissingPanels(self):
        layout = DockLayout(smallLayout())
        assert layout.load({
            "version": LAYOUT_VERSION,
            "main": {"type": "tabs", "panels": ["c", "unknown", "c", "a", 42], "current": "unknown"},
            "closed": ["unknown", "a"],
        })
        checkNormalized(layout)
        # "b" and "d" go back to the group of their default siblings, "c" and "a" being in the only group
        assert groups(layout) == [["c", "a", "b", "d"]]
        assert layout.groupOf("a")["current"] == "c"
        assert layout.openPanels() == ["b", "c", "d"]

    def test_emptyLayoutFallsBackToDefaultGroups(self):
        layout = DockLayout(smallLayout())
        assert layout.load({"version": LAYOUT_VERSION, "main": None})
        checkNormalized(layout)
        assert groups(layout) == [["a", "b", "c", "d"]]

    def test_malformedNodesAreCleanedUp(self):
        layout = DockLayout(smallLayout())
        assert layout.load({
            "version": LAYOUT_VERSION,
            "main": {
                "type": "split", "orientation": "diagonal", "sizes": [1, "big", 2],
                "children": [
                    {"type": "tabs", "panels": ["a"]},
                    {"type": "split", "orientation": HORIZONTAL, "sizes": [0.5, 0.5],
                     "children": [{"type": "tabs", "panels": ["b"]}, {"type": "tabs", "panels": ["c"]}]},
                    {"type": "split", "orientation": VERTICAL, "children": [{"type": "tabs", "panels": ["d"]}, "garbage"]},
                    {"type": "unknown", "panels": ["x"]},
                ],
            },
            "closed": "garbage",
        })
        checkNormalized(layout)
        main = layout.toDict()["main"]
        # Invalid orientation falls back to horizontal, then the nested horizontal split is merged in it,
        # and the vertical split left with a single child collapses into that child
        assert main["orientation"] == HORIZONTAL
        assert [child["panels"] for child in main["children"]] == [["a"], ["b"], ["c"], ["d"]]
        assert main["sizes"] == [1 / 3, 1 / 6, 1 / 6, 1 / 3]
        assert layout.openPanels() == PANELS

    def test_duplicatedIdsAreReplaced(self):
        layout = DockLayout(smallLayout())
        data = layout.toDict()
        data["main"]["children"][1]["id"] = data["main"]["children"][0]["id"]
        assert layout.load(data)
        checkNormalized(layout)
        # New ids do not collide with the loaded ones
        layout.movePanel("a", layout.groupOf("c")["id"], "top")
        checkNormalized(layout)


class TestLegacySettings:

    def test_noSettingsKeepsTheDefault(self):
        layout = DockLayout()
        applyLegacySettings(layout, {})
        assert layout.toDict() == DockLayout().toDict()

    def test_visibilityFlags(self):
        layout = DockLayout()
        applyLegacySettings(layout, {"showViewer3D": "false", "showTextViewer": "true", "showImageGallery": True})
        assert not layout.isOpen("viewer3D")
        assert layout.isOpen("textViewer")
        assert layout.isOpen("imageGallery")

    def test_hiddenGraphEditorHidesTheWholeBottomPart(self):
        layout = DockLayout()
        applyLegacySettings(layout, {"showGraphEditor": "false"})
        assert layout.openPanels() == ["imageGallery", "imageViewer", "viewer3D"]
