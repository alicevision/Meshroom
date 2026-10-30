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

        // Sizes are all set explicitly, as the headers only follow explicit sizes.
        // Automatic widths are kept to tell them apart from the ones set by the user.
        property var autoColumnWidths: []
        // Largest content measured so far: TableView only measures loaded cells, and columns and rows
        // must not shrink when they are scrolled out of the view
        property var contentColumnWidths: []
        property var contentRowHeights: []

        function updateColumnWidths() {
            const stretchedWidth = (width - rightMargin) / columns
            let totalWidth = 0
            for (let column = 0; column < columns; column++) {
                contentColumnWidths[column] = Math.max(contentColumnWidths[column] || 0, implicitColumnWidth(column),
                                                       horizontalHeader.implicitColumnWidth(column))
                let columnWidth = explicitColumnWidth(column)
                if (columnWidth < 0 || columnWidth === autoColumnWidths[column]) {
                    const autoWidth = Math.max(contentColumnWidths[column], root.minColumnWidth, stretchedWidth)
                    // Only set changed widths, as each change triggers a new layout
                    if (autoWidth !== columnWidth) {
                        autoColumnWidths[column] = autoWidth
                        setColumnWidth(column, autoWidth)
                    }
                    columnWidth = autoWidth
                }
                totalWidth += columnWidth
            }
            // Instead of TableView's estimate from the loaded columns, which makes the scroll bar jump
            contentWidth = totalWidth
        }

        function updateRowHeights() {
            for (let row = 0; row < rows; row++) {
                contentRowHeights[row] = Math.max(contentRowHeights[row] || 0, implicitRowHeight(row),
                                                  verticalHeader.implicitRowHeight(row))
                // Rows that have never been loaded can't be measured yet
                if (contentRowHeights[row] > 0 && contentRowHeights[row] !== explicitRowHeight(row))
                    setRowHeight(row, contentRowHeights[row])
            }
        }

        onWidthChanged: Qt.callLater(updateColumnWidths)
        onLayoutChanged: {
            Qt.callLater(updateColumnWidths)
            Qt.callLater(updateRowHeights)
        }
        onColumnsChanged: {
            clearColumnWidths()
            autoColumnWidths = []
            contentColumnWidths = []
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
