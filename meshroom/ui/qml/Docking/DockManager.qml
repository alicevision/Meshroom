import QtQuick

/**
 * DockManager displays the DockPanels of the application in DockAreas, following the dock layout of
 * `layoutModel` (see meshroom/ui/dockLayoutManager.py): the DockArea of the main window, and a
 * DockWindow for each floating window. It lets the user move the panels by dragging their tabs,
 * including out of the windows to float them.
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
        /// DockWindows by id of floating window
        property var windows: ({})
    }

    Connections {
        target: root.layoutModel
        // Never rebuild while handling an event of an item that the rebuild destroys (e.g. a tab)
        function onLayoutChanged() { Qt.callLater(root.rebuild) }
    }

    Component.onCompleted: rebuild()
    // The floating windows have no parent (see createWindow), they have to be destroyed explicitly
    Component.onDestruction: {
        for (var windowId in m.windows)
            m.windows[windowId].destroy()
    }

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

    /// Return the ids of the panels of a node of the layout and of its descendants
    function panelsOf(node) {
        if (!node)
            return []
        if (node.type === "tabs")
            return node.panels
        return node.children.reduce(function(panelIds, child) { return panelIds.concat(panelsOf(child)) }, [])
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

        // Keep the windows still in the layout, create the new ones
        var windows = {}
        layout.floating.forEach(function(entry) {
            var window = m.windows[entry.id] || createWindow(entry)
            delete m.windows[entry.id]
            window.entry = entry
            window.area.setRootNode(entry.root)
            windows[entry.id] = window
        })
        var removedWindows = m.windows
        m.windows = windows

        m.groups.forEach(function(group) { group.hostPanels() })
        // The removed windows are empty now: all the panels are displayed somewhere else
        for (var windowId in removedWindows)
            removedWindows[windowId].destroy()
    }

    function createWindow(entry) {
        var mainWindow = mainArea.Window.window
        var geometry = entry.geometry || [mainWindow.x + mainWindow.width / 2 - 300, mainWindow.y + mainWindow.height / 2 - 200, 600, 400]
        // Created from its url: a DockWindow type dependency would be cyclic. Without a parent: it is
        // transient for the main window anyway, and a window created with a parent item triggers a
        // warning in Meshroom. The reference kept in m.windows prevents its garbage collection.
        var component = Qt.createComponent(Qt.resolvedUrl("DockWindow.qml"))
        return component.createObject(null, {
            "manager": root,
            "entry": entry,
            // Keep the shortcuts of the main window working while the floating window is active
            "transientParent": mainWindow,
            "palette": mainWindow.palette,
            "x": geometry[0],
            "y": geometry[1],
            "width": geometry[2],
            "height": geometry[3]
        })
    }

    /**
     * Move a panel to a new floating window, with its top left corner at the given global position.
     * A panel already alone in a floating window moves that window instead.
     */
    function floatPanel(panel, globalX, globalY) {
        if (!layoutModel.canFloat(panel.panelId))
            return
        var group = panel.dockGroup
        if (layoutModel.floatPanel(panel.panelId, globalX, globalY, Math.max(group.width, 300), Math.max(group.height, 200)))
            return
        var window = group.Window.window
        if (window !== mainArea.Window.window) {
            window.x = globalX
            window.y = globalY
        }
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

    /// Drop the dragged panel at the given global position: released out of any window, it floats
    function endDrag(globalX, globalY) {
        var panel = draggedPanel
        if (!panel)
            return
        var target = dropTargetAt(globalX, globalY)
        var window = layoutModel.windowAt(globalX, globalY)
        cancelDrag()
        if (target)
            layoutModel.movePanel(panel.panelId, target.group.node.id, target.zone, target.index)
        else if (!window)
            // Keep the tab under the cursor, as if it had been torn off
            floatPanel(panel, globalX - 40, globalY - 14)
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
        if (target.group.area !== mainArea && !layoutModel.canFloat(draggedPanel.panelId))
            return false
        if (target.group !== draggedPanel.dockGroup)
            return true
        // On its own group, the panel can only be moved to another tab position, or beside the group
        // if other panels remain in it
        if (target.zone === "center")
            return target.index >= 0
        return target.group.node.panels.length > 1
    }
}
