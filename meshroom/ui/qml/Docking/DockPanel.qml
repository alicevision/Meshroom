import QtQuick

/**
 * DockPanel wraps a panel of the application so that a DockManager can dock it: display it as a tab
 * of a DockGroup, and move it to another group when the user drags its tab.
 *
 * The panel is instantiated once and then only reparented, so it keeps its state wherever it is
 * displayed. Its content is declared as children, filling it.
 */

Item {
    id: root

    /// Unique id of the panel in the dock layout (see meshroom/ui/dockLayout.py)
    property string panelId
    /// Name of the panel, used in menus and as the default text of its tab
    property string title
    /// Text of the tab; may be styled text
    property string tabTitle: title
    /// Contextual toolbar, displayed in the header of the DockGroup while the panel is its current tab
    property Item toolBar: null

    /// The DockGroup currently displaying the panel, set by the DockManager
    property Item dockGroup: null
    /// Whether the panel is open, bound by the DockManager
    property bool isOpen: false

    /// Put the toolbar back in the panel, hidden
    function parkToolBar() {
        if (toolBar)
            toolBar.parent = toolBarParking
    }

    Component.onCompleted: parkToolBar()

    Item {
        id: toolBarParking
        visible: false
    }
}
