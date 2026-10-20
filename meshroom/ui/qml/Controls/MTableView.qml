import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * MTableView displays a table model with column headers, resizable columns and scroll bars.
 * It is agnostic of the model's content: cells are instantiated with 'delegate', and rows can
 * optionally get a header with 'rowHeaderDelegate' (e.g. to hold actions on the row).
 * Columns stretch to fill the view until they are resized by the user.
 * Ctrl + mouse wheel scrolls horizontally.
 */

GridLayout {
    id: root
    columns: 2
    rowSpacing: 0
    columnSpacing: 0

    property alias model: tableView.model
    property alias delegate: tableView.delegate
    // Disable for delegates that write to the model, which could otherwise act on their new cell when reused
    property alias reuseItems: tableView.reuseItems
    property Component rowHeaderDelegate: null
    // Optional item in the top-left corner, above the rows' headers
    property Component cornerDelegate: null
    property real minColumnWidth: 60

    Loader {
        Layout.row: 0
        Layout.column: 0
        // Keep the corner item's own size when the headers are empty
        Layout.preferredWidth: Math.max(verticalHeader.implicitWidth, implicitWidth)
        Layout.preferredHeight: Math.max(horizontalHeader.implicitHeight, implicitHeight)
        visible: verticalHeader.visible
        sourceComponent: root.cornerDelegate
    }

    HorizontalHeaderView {
        id: horizontalHeader
        Layout.row: 0
        Layout.column: 1
        Layout.fillWidth: true
        syncView: tableView
        // syncView alone does not keep the header aligned when scrolling with the scroll bar: follow it explicitly
        contentX: tableView.contentX
        resizableColumns: true
        clip: true
    }

    VerticalHeaderView {
        id: verticalHeader
        Layout.row: 1
        Layout.column: 0
        Layout.fillHeight: true
        visible: root.rowHeaderDelegate !== null
        syncView: tableView
        contentY: tableView.contentY
        resizableRows: false
        delegate: root.rowHeaderDelegate
        clip: true
    }

    TableView {
        id: tableView
        Layout.row: 1
        Layout.column: 1
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        // Keep the scroll bars from overlapping the cells.
        rightMargin: verticalScrollBar.width
        bottomMargin: horizontalScrollBar.height

        // Columns' widths are all set explicitly, as the header only follows explicit widths.
        // The widths set automatically are kept to tell them apart from the ones set by the user.
        property var autoColumnWidths: []

        function updateColumnWidths() {
            const stretchedWidth = (width - rightMargin) / columns
            for (let column = 0; column < columns; column++) {
                const explicitWidth = explicitColumnWidth(column)
                if (explicitWidth >= 0 && explicitWidth !== autoColumnWidths[column])
                    continue
                const autoWidth = Math.max(implicitColumnWidth(column), horizontalHeader.implicitColumnWidth(column),
                                           root.minColumnWidth, stretchedWidth)
                // Only set changed widths, as each change triggers a new layout
                if (autoWidth !== explicitWidth) {
                    autoColumnWidths[column] = autoWidth
                    setColumnWidth(column, autoWidth)
                }
            }
        }

        onWidthChanged: Qt.callLater(updateColumnWidths)
        onLayoutChanged: Qt.callLater(updateColumnWidths)
        onColumnsChanged: {
            clearColumnWidths()
            autoColumnWidths = []
            Qt.callLater(updateColumnWidths)
        }

        ScrollBar.horizontal: MScrollBar { id: horizontalScrollBar }
        ScrollBar.vertical: MScrollBar { id: verticalScrollBar }

        WheelHandler {
            acceptedModifiers: Qt.ControlModifier
            onWheel: (event) => {
                const delta = event.angleDelta.y / 120 * 40
                tableView.contentX = Math.max(0, Math.min(tableView.contentWidth + tableView.rightMargin - tableView.width, tableView.contentX - delta))
                event.accepted = true
            }
        }
    }
}
