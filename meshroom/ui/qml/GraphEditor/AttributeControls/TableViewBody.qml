import QtQuick
import QtQuick.Controls

import MaterialIcons 2.2
import Utils 1.0
import Controls 1.0

/**
 * Renders the header, rows and scrollbars for a "table" ListAttribute (a ListAttribute
 * of GroupAttribute). Self-contained so it can be instantiated more than once for the
 * same `attribute` (e.g. inline in the attribute editor and in a fullscreen window)
 * without the instances interfering with each other.
 */
Item {
    id: root

    required property var attribute
    property bool editable: true
    property real stdHeight: 24
    // Whether this instance is the one shown in the fullscreen window (shows an extra
    // "Add Element" button in the top-left corner, since the inline instance already
    // has one in its header row).
    property bool isFullscreen: false

    property var columnNames: {
        if (!attribute || !attribute.value || attribute.value.count === 0)
            return []
        var firstRow = attribute.value.at(0)
        if (!firstRow || !firstRow.value)
            return []
        var names = []
        for (var i = 0; i < firstRow.value.count; i++) {
            var child = firstRow.value.at(i)
            if (child)
                names.push(child.label)
        }
        return names
    }
    property var columnWidths: []
    readonly property real totalTableHeight: attribute && attribute.value
                                    ? attribute.value.count * 31
                                    : 0
    property var scaledColumnWidths: []
    property real scaledTableWidth: 0
    property real availableW: root.width > 0
                              ? root.width - fixedStrip.width
                              : 600
    // Size that fits the table's content, used to size the fullscreen window on open.
    readonly property real preferredContentWidth: scaledTableWidth + fixedStrip.width + vBar.width + 2 * stdHeight
    readonly property real preferredContentHeight: totalTableHeight + hBar.height + 0.5 * stdHeight

    function computeMinColumnWidths() {
        var firstRow = rowRepeater.itemAt(0)
        if (!firstRow || firstRow.minColumnWidths.length === 0)
            return new Array(root.columnNames.length).fill(60)
        return firstRow.minColumnWidths
    }
    function updateScaledWidths() {
        if (!root.columnWidths || root.columnWidths.length === 0)
            return
        var n = root.columnWidths.length
        var mins = computeMinColumnWidths()
        var widths = [], total = 0
        for (var i = 0; i < n; i++) {
            var minW = (mins[i] !== undefined ? mins[i] : 60)
            var w = Math.max(root.columnWidths[i], minW)
            widths.push(w)
            total += w
        }
        var leftover = root.availableW - total
        if (leftover > 0.5 && n > 0) {
            var share = leftover / n
            for (var j = 0; j < n; j++)
                widths[j] += share
        }
        total = 0
        for (var l = 0; l < n; l++)
            total += widths[l]
        root.scaledColumnWidths = widths
        root.scaledTableWidth = total
    }
    FontMetrics { id: fontMetrics; font.bold: true }
    function initSizes() {
        var names = root.columnNames
        if (!names || names.length === 0) {
            root.columnWidths = []
            return
        }
        var widths = []
        for (var i = 0; i < names.length; i++)
            widths.push(fontMetrics.advanceWidth(names[i]) + 20)
        if (attribute && attribute.value) {
            for (var r = 0; r < attribute.value.count; r++) {
                var rowAttr = attribute.value.at(r)
                if (!rowAttr || !rowAttr.value)
                    continue
                for (var c = 0; c < rowAttr.value.count && c < widths.length; c++) {
                    var ca = rowAttr.value.at(c)
                    var cw = fontMetrics.advanceWidth(ca ? String(ca.value) : "") + 20
                    if (cw > widths[c])
                        widths[c] = cw
                }
            }
        }
        root.columnWidths = widths
    }
    Component.onCompleted: {
        initSizes()
        updateScaledWidths()
    }
    Connections {
        target: attribute
                ? attribute.value
                : null
        function refreshSizes() { root.initSizes(); root.updateScaledWidths() }
        function onCountChanged() { refreshSizes() }
        function onModelReset() { refreshSizes() }
        function onRowsInserted() { refreshSizes() }
        function onDataChanged() { refreshSizes() }
    }
    onAvailableWChanged: root.updateScaledWidths()

    Item {
        id: fixedHeader
        anchors {
            left: fixedStrip.right
            right: root.right
            top: root.top
        }
        height: stdHeight
        clip: true
        Row {
            spacing: 1
            x: -flickable.contentX
            Repeater {
                model: root.columnNames
                delegate: Item {
                    id: headerCell
                    required property int index
                    required property string modelData
                    width: root.scaledColumnWidths[index] || 100
                    height: stdHeight
                    Rectangle {
                        anchors.fill: parent
                        color: Qt.darker(palette.window, 1.2)
                        border.color: palette.mid
                        Text {
                            anchors.fill: parent
                            text: headerCell.modelData
                            color: palette.text
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                    MouseArea {
                        id: colResizeHandle
                        width: 6
                        height: parent.height
                        anchors.right: parent.right
                        cursorShape: Qt.SizeHorCursor
                        preventStealing: true
                        property real startX: 0
                        property real startW: 0
                        onPressed: function(mouse) {
                            var p = mapToItem(root, mouse.x, mouse.y)
                            startX = p.x
                            startW = root.columnWidths[headerCell.index] || 100
                        }
                        onPositionChanged: function(mouse) {
                            if (!pressed)
                                return
                            var p = mapToItem(root, mouse.x, mouse.y)
                            var delta = p.x - startX
                            var newW = startW + delta
                            var mins = root.computeMinColumnWidths()
                            var minW = Math.max(40,
                                           mins[headerCell.index] !== undefined
                                           ? mins[headerCell.index]
                                           : 60)
                            newW = Math.max(minW, newW)
                            var wa = root.columnWidths.slice()
                            wa[headerCell.index] = newW
                            root.columnWidths = wa
                            root.updateScaledWidths()
                        }
                    }
                }
            }
        }
    }
    Item {
        id: fixedStrip
        anchors {
            left: root.left
            top: root.top
            bottom: root.bottom
            topMargin: stdHeight
        }
        width: stdHeight
        clip: true
        Column {
            spacing: 1
            width: parent.width
            y: -flickable.contentY
            Repeater {
                model: attribute
                       ? attribute.value
                       : null
                delegate: Item {
                    id: removeDelegate
                    required property int index
                    required property var object
                    width: fixedStrip.width
                    height: stdHeight
                    RemoveElementButton {
                        anchors.centerIn: parent
                        editable: root.editable
                        onClicked: _currentScene.removeAttribute(removeDelegate.object)
                    }
                }
            }
        }
    }
    Item {
        id: cornerCell
        anchors {
            left: root.left
            top: root.top
        }
        width: fixedStrip.width
        height: fixedHeader.height
        visible: root.isFullscreen
        Rectangle {
            anchors.fill: parent
            color: Qt.darker(palette.window, 1.2)
            border.color: palette.mid
        }
        AddElementButton {
            anchors.centerIn: parent
            editable: root.editable
            onClicked: _currentScene.appendAttribute(root.attribute, undefined)
        }
    }
    Flickable {
        id: flickable
        anchors {
            left: fixedStrip.right
            right: root.right
            top: root.top
            bottom: root.bottom
            topMargin: stdHeight
        }
        clip: true
        contentWidth: root.scaledTableWidth
        contentHeight: root.totalTableHeight
        interactive: true
        ScrollBar.horizontal: MScrollBar { id: hBar }
        ScrollBar.vertical: MScrollBar { id: vBar }
        WheelHandler {
            onWheel: function(event) {
                if (event.modifiers & Qt.ControlModifier) {
                    flickable.contentX = Math.max(0,
                        Math.min(flickable.contentWidth - flickable.width,
                                 flickable.contentX -
                                     event.angleDelta.y / 120 * 40))
                } else {
                    flickable.contentY = Math.max(0,
                        Math.min(flickable.contentHeight - flickable.height,
                                 flickable.contentY -
                                     event.angleDelta.y / 120 * 40))
                }
                event.accepted = true
            }
        }
        Column {
            spacing: 1
            Repeater {
                id: rowRepeater
                model: attribute
                       ? attribute.value
                       : null
                delegate: TableViewRowDelegate {
                    rowIndex: index
                    rowObject: object
                    rowHeight: stdHeight
                    tableWidth: root.scaledTableWidth
                    scaledColumnWidths: root.scaledColumnWidths
                    editable: root.editable
                }
            }
        }
    }
}
