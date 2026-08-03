import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import MaterialIcons 2.2
import Utils 1.0 

ColumnLayout {
    id: root
    spacing: 0
    property bool editable: true
    required property var attribute
    property real stdHeight: 24
    property var columnNames: {
        if (!attribute || !attribute.value || attribute.value.count === 0)
            return []
        var firstRow = attribute.value.at(0)
        if (!firstRow || !firstRow.value) return []
        var names = []
        for (var i = 0; i < firstRow.value.count; i++) {
            var child = firstRow.value.at(i)
            if (child) names.push(child.label)
        }
        return names
    }
    property var columnWidths: []
    property real totalTableWidth: {
        if (!columnWidths || columnWidths.length === 0)
            return 0
        var t = 0
        for (var i = 0; i < columnWidths.length; i++) t += columnWidths[i]
        t += Math.max(0, columnWidths.length - 1)
        return t
    }
    property real totalTableHeight: attribute && attribute.value
                                    ? attribute.value.count * 31
                                    : 0
    property var scaledColumnWidths: []
    property real scaledTableWidth: 0
    property real availableW: outerFrame.width > 0 
                              ? outerFrame.width - fixedStrip.width - vBar.width
                              : 600
    function computeMinColumnWidths() {
        var firstRow = rowRepeater.itemAt(0)
        if (!firstRow)
            return new Array(root.columnNames.length).fill(60)
        return firstRow.minColumnWidths
    }
    function computeMaxColumnWidths() {
        var firstRow = rowRepeater.itemAt(0)
        var n = root.columnWidths.length
        if (!firstRow || !firstRow.maxColumnWidths || firstRow.maxColumnWidths.length !== n)
            return new Array(n).fill(Infinity)
        return firstRow.maxColumnWidths.map(function(v, i) {
            return v === Infinity ? Infinity : root.columnWidths[i] * 1.2
        })
    }
    function updateScaledWidths() {
        if (!root.columnWidths || root.columnWidths.length === 0)
            return
        var mins = computeMinColumnWidths()
        var maxs = computeMaxColumnWidths()
        var n = root.columnWidths.length
        var total = 0
        var widths = []
        for (var i = 0; i < n; i++) {
            var w = Math.max(root.columnWidths[i], mins[i] !== undefined ? mins[i] : 60)
            widths.push(w)
            total += w
        }
        var leftover = root.availableW - total
        if (leftover > 0) {
            var eligible = []
            for (var j = 0; j < n; j++) {
                if (maxs[j] === undefined || maxs[j] === Infinity || widths[j] < maxs[j])
                    eligible.push(j)
            }
            while (leftover > 0.5 && eligible.length > 0) {
                var extra = leftover / eligible.length
                var stillEligible = []
                var consumed = 0
                for (var k = 0; k < eligible.length; k++) {
                    var idx = eligible[k]
                    var cap = (maxs[idx] === undefined || maxs[idx] === Infinity)
                               ? Infinity
                               : maxs[idx]
                    var room = (cap === Infinity) ? Infinity : cap - widths[idx]
                    if (cap !== Infinity && room <= extra) {
                        widths[idx] = cap
                        consumed += room
                    } else {
                        widths[idx] += extra
                        consumed += extra
                        stillEligible.push(idx)
                    }
                }
                leftover -= consumed
                eligible = stillEligible
            }
        }
        total = 0
        for (var l = 0; l < n; l++)
            total += widths[l]
        root.scaledColumnWidths = widths
        root.scaledTableWidth = total
    }
    property bool expanded: false
    property var appPalette: palette
    RowLayout {
        spacing: 4
        ToolButton {
            text: root.expanded
                  ? MaterialIcons.keyboard_arrow_down
                  : MaterialIcons.keyboard_arrow_right
            font.family: MaterialIcons.fontFamily
            onClicked: root.expanded = !root.expanded
        }
        Label {
            Layout.alignment: Qt.AlignVCenter
            text: attribute.value.count + " elements"
        }
        ToolButton {
            text: MaterialIcons.add_circle_outline
            font.family: MaterialIcons.fontFamily
            font.pointSize: 11
            padding: 2
            enabled: root.editable
            onClicked: _currentScene.appendAttribute(attribute, undefined)
        }
        ToolButton {
            text: MaterialIcons.fullscreen
            font.family: MaterialIcons.fontFamily
            font.pointSize: 11
            padding: 2
            ToolTip.text: "Open in fullscreen"
            ToolTip.visible: hovered
            onClicked: {
                outerFrame.Layout.preferredWidth = -1
                outerFrame.Layout.preferredHeight = -1
                outerFrame.visible = true
                outerFrame.parent = fullscreenContent
                outerFrame.anchors.fill = fullscreenContent
                outerFrame.isFullscreen = true
                fullscreenWindow.width  = root.scaledTableWidth + fixedStrip.width + vBar.width + 2*stdHeight
                fullscreenWindow.height = root.totalTableHeight + hBar.height + 0.75*stdHeight
                fullscreenWindow.show()
            }
        }
    }
    Window {
        id: fullscreenWindow
        title: attribute
               ? attribute.label
               : ""
        palette: root.appPalette
        color: palette.window
        Item {
            id: fullscreenContent
            anchors.fill: parent
        }
        onClosing: {
            outerFrame.anchors.fill = undefined
            outerFrame.width = undefined
            outerFrame.height = undefined
            outerFrame.Layout.preferredWidth = -1
            outerFrame.parent = root
            outerFrame.isFullscreen = false
            outerFrame.Layout.fillWidth = true
            outerFrame.Layout.preferredHeight = Qt.binding(function() {
                return root.expanded
                       ? Math.min(root.totalTableHeight + 40, 330)
                       : 0
            })
            outerFrame.visible = Qt.binding(function() {
                return root.expanded
            })
        }
    }
    FontMetrics {
        id: fontMetrics
        font.bold: true
    }
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
                if (!rowAttr || !rowAttr.value) continue
                for (var c = 0; c < rowAttr.value.count && c < widths.length; c++) {
                    var cell = rowAttr.value.at(c)
                    var cellText = cell ? String(cell.value) : ""
                    var cw = fontMetrics.advanceWidth(cellText) + 20
                    if (cw > widths[c]) widths[c] = cw
                }
            }
        }
        root.columnWidths = widths
    }
    Component.onCompleted: {
        root.initSizes()
        root.updateScaledWidths()
    }
    Connections {
        target: attribute
                ? attribute.value
                : null
        function onCountChanged() {root.initSizes(); root.updateScaledWidths()}
        function onModelReset() {root.initSizes(); root.updateScaledWidths()}
        function onRowsInserted() {root.initSizes(); root.updateScaledWidths()}
        function onDataChanged() {root.initSizes(); root.updateScaledWidths()}
    }
    onAvailableWChanged: root.updateScaledWidths()
    Item {
        id: outerFrame
        Layout.fillWidth: true
        visible: root.expanded
        Layout.preferredHeight: root.expanded
                                ? Math.min(root.totalTableHeight + 40, 330)
                                : 0
        property bool isFullscreen: false
        ScrollBar {
            id: hBar
            anchors.left: fixedStrip.right
            anchors.right: outerFrame.right
            anchors.bottom: outerFrame.bottom
            anchors.rightMargin: vBar.width
            orientation: Qt.Horizontal
            policy: flickable.contentWidth > flickable.width
                    ? ScrollBar.AlwaysOn
                    : ScrollBar.AlwaysOff
            size: Math.min(1.0, flickable.width / Math.max(flickable.contentWidth, 1))
            position: (flickable.contentX / Math.max(flickable.contentWidth - flickable.width, 1))
                      * (1.0 - size)
            onPositionChanged: {
                if (!pressed) return
                var maxPos = 1.0 - size
                var ratio = maxPos > 0 ? position / maxPos : 0
                flickable.contentX = ratio * Math.max(flickable.contentWidth - flickable.width, 1)
            }
        }
        ScrollBar {
            id: vBar
            anchors.top: outerFrame.top
            anchors.bottom: outerFrame.bottom
            anchors.right: outerFrame.right
            anchors.bottomMargin: hBar.height
            orientation: Qt.Vertical
            policy: flickable.contentHeight > flickable.height
                    ? ScrollBar.AlwaysOn
                    : ScrollBar.AlwaysOff
            size: Math.min(1.0, flickable.height / Math.max(flickable.contentHeight, 1))
            position: (flickable.contentY / Math.max(flickable.contentHeight - flickable.height, 1))
                      * (1.0 - size)
            onPositionChanged: {
                if (!pressed) return
                var maxPos = 1.0 - size
                var ratio = maxPos > 0 ? position / maxPos : 0
                flickable.contentY = ratio * Math.max(flickable.contentHeight - flickable.height, 1)
            }
        }
        Item {
            id: fixedHeader
            anchors.left: fixedStrip.right
            anchors.right: outerFrame.right
            anchors.top: outerFrame.top
            anchors.rightMargin: vBar.width
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
                                startW = root.columnWidths[headerCell.index]
                            }
                            onReleased: function(mouse) { }
                            onPositionChanged: function(mouse) {
                                if (!pressed) return
                                var p = mapToItem(root, mouse.x, mouse.y)
                                var minW = Math.max(40, computeMinColumnWidths()[headerCell.index] || 60)
                                var newW = Math.max(minW, startW + (p.x - startX))
                                var widthArray = root.columnWidths.slice()
                                widthArray[headerCell.index] = newW
                                root.columnWidths = widthArray
                                root.updateScaledWidths()
                            }
                        }
                    }
                }
            }
        }
        Item {
            id: fixedStrip
            anchors.left: outerFrame.left
            anchors.top: outerFrame.top
            anchors.bottom: hBar.top
            anchors.topMargin: stdHeight
            width: stdHeight
            clip: true
            Column {
                spacing: 1
                width: parent.width
                y: -flickable.contentY
                Repeater {
                    model: attribute ? attribute.value : null
                    delegate: Item {
                        id: removeDelegate
                        required property int index
                        required property var object
                        width: fixedStrip.width
                        height: stdHeight
                        ToolButton {
                            anchors.centerIn: parent
                            enabled: root.editable
                            text: MaterialIcons.remove_circle_outline
                            font.family: MaterialIcons.fontFamily
                            font.pointSize: 11
                            padding: 2
                            ToolTip.text: "Remove Element"
                            ToolTip.visible: hovered
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: palette.text
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            onClicked: _currentScene.removeAttribute(removeDelegate.object)
                        }
                    }
                }
            }
        }
        Item {
            id: cornerCell
            anchors.left: outerFrame.left
            anchors.top: outerFrame.top
            width: fixedStrip.width
            height: fixedHeader.height
            visible: outerFrame.isFullscreen
            Rectangle {
                anchors.fill: parent
                color: Qt.darker(palette.window, 1.2)
                border.color: palette.mid
            }
            ToolButton {
                anchors.centerIn: parent
                text: MaterialIcons.add_circle_outline
                font.family: MaterialIcons.fontFamily
                font.pointSize: 11
                padding: 2
                enabled: root.editable
                ToolTip.text: "Add Element"
                ToolTip.visible: hovered
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: palette.text
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: _currentScene.appendAttribute(attribute, undefined)
            }
        }
        Flickable {
            id: flickable
            anchors.left: fixedStrip.right
            anchors.top: outerFrame.top
            anchors.right: outerFrame.right
            anchors.bottom: hBar.top
            anchors.topMargin: stdHeight
            anchors.rightMargin: vBar.width
            clip: true
            contentWidth: root.scaledTableWidth
            contentHeight: root.totalTableHeight
            interactive: true
            WheelHandler {
                onWheel: function(event) {
                    if (event.modifiers & Qt.ControlModifier) {
                        flickable.contentX = Math.max(0,
                            Math.min(flickable.contentWidth - flickable.width,
                                     flickable.contentX - event.angleDelta.y / 120 * 40))
                    } else {
                        flickable.contentY = Math.max(0,
                            Math.min(flickable.contentHeight - flickable.height,
                                     flickable.contentY - event.angleDelta.y / 120 * 40))
                    }
                    event.accepted = true
                }
            }
            Column {
                spacing: 1
                Repeater {
                    id: rowRepeater
                    model: attribute ? attribute.value : null
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
}
