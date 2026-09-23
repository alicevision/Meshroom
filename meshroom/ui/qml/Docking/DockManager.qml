import QtQuick

/**
 * DockManager displays the DockPanels of the application in DockAreas, following the dock layout of
 * `layoutModel` (see meshroom/ui/dockLayoutManager.py), and lets the user move them by dragging
 * their tabs.
 *
 * Panels are never destroyed: whenever the structure of the layout changes, the areas are rebuilt
 * and the panels are reparented into the new groups of tabs, keeping their state.
 */

Item {
    id: root

    /// The DockLayoutManager holding the layout
    property var layoutModel
    /// The DockPanels to display, each one having a unique panelId
    property var panelList: []
    /// The DockArea of the main window
    property Item mainArea

    /// DockPanels by panelId
    readonly property var panels: {
        var byId = {}
        panelList.forEach(function(panel) { byId[panel.panelId] = panel })
        return byId
    }

    /// The panel being dragged by its tab, if any
    property DockPanel draggedPanel: null
    /// Where the dragged panel would be dropped (see DockGroup.dropZoneAt), or null
    property var dropTarget: null
    /// The area under the cursor while a panel is dragged, and the position of the cursor in it
    property Item ghostArea: null
    property point ghostPosition

    visible: false

    QtObject {
        id: m
        property var areas: []
        property var groups: []
    }

    Connections {
        target: root.layoutModel
        // Never rebuild while handling an event of an item that the rebuild destroys (e.g. a tab)
        function onLayoutChanged() { Qt.callLater(root.rebuild) }
    }

    Component.onCompleted: rebuild()

    function registerArea(area) { m.areas.push(area) }
    function unregisterArea(area) { m.areas = m.areas.filter(function(a) { return a !== area }) }
    function registerGroup(group) { m.groups.push(group) }
    function unregisterGroup(group) { m.groups = m.groups.filter(function(g) { return g !== group }) }

    /// Whether a node of the layout contains an open panel, i.e. has to be displayed
    function hasOpenPanel(node) {
        var open = layoutModel.openPanels
        if (!node)
            return false
        if (node.type === "tabs")
            return node.panels.some(function(panelId) { return open.indexOf(panelId) !== -1 })
        return node.children.some(hasOpenPanel)
    }

    /// Return the DockArea of the window displaying an item
    function areaOf(item) {
        var window = item.Window.window
        for (var i = 0; i < m.areas.length; ++i) {
            if (m.areas[i].Window.window === window)
                return m.areas[i]
        }
        return mainArea
    }

    /// Hide a panel in the parking item of its window
    function park(panel) {
        panel.parkToolBar()
        panel.anchors.fill = undefined
        panel.parent = areaOf(panel).parking
        panel.dockGroup = null
    }

    /// Display the current layout, reparenting every panel into its group of tabs
    function rebuild() {
        if (!mainArea || !layoutModel)
            return
        cancelDrag()
        var layout = layoutModel.layout
        // Park the panels first: rebuilding the areas destroys the current groups of tabs, which are
        // removed from their window right away
        for (var panelId in panels)
            park(panels[panelId])
        m.groups.forEach(function(group) { group.retired = true })
        m.groups = []
        mainArea.setRootNode(layout.main)
        m.groups.forEach(function(group) { group.hostPanels() })
    }

    // --- Drag and drop of the tabs -------------------------------------------------------------

    /// Update the drop target and the label following the cursor, at the given global position
    function updateDrag(globalX, globalY) {
        if (!draggedPanel)
            return
        var target = dropTargetAt(globalX, globalY)
        if (!target || !dropTarget || target.group !== dropTarget.group || target.zone !== dropTarget.zone || target.index !== dropTarget.index)
            dropTarget = target

        var window = layoutModel.windowAt(globalX, globalY)
        ghostArea = null
        for (var i = 0; i < m.areas.length; ++i) {
            if (m.areas[i].Window.window === window) {
                ghostArea = m.areas[i]
                ghostPosition = ghostArea.mapFromGlobal(globalX, globalY)
            }
        }
    }

    /// Drop the dragged panel at the given global position
    function endDrag(globalX, globalY) {
        var panel = draggedPanel
        var target = panel ? dropTargetAt(globalX, globalY) : null
        cancelDrag()
        if (target)
            layoutModel.movePanel(panel.panelId, target.group.node.id, target.zone, target.index)
    }

    function cancelDrag() {
        draggedPanel = null
        dropTarget = null
        ghostArea = null
    }

    /// Return where the dragged panel would be dropped at the given global position, or null
    function dropTargetAt(globalX, globalY) {
        var window = layoutModel.windowAt(globalX, globalY)
        if (!window)
            return null
        for (var i = 0; i < m.groups.length; ++i) {
            var group = m.groups[i]
            if (group.retired || !group.visible || group.Window.window !== window)
                continue
            var position = group.mapFromGlobal(globalX, globalY)
            if (position.x < 0 || position.y < 0 || position.x >= group.width || position.y >= group.height)
                continue
            var target = group.dropZoneAt(position.x, position.y)
            return isDropAllowed(target) ? target : null
        }
        return null
    }

    function isDropAllowed(target) {
        if (target.group !== draggedPanel.dockGroup)
            return true
        // On its own group, the panel can only be moved to another tab position, or beside the group
        // if other panels remain in it
        if (target.zone === "center")
            return target.index >= 0
        return target.group.node.panels.length > 1
    }
}
