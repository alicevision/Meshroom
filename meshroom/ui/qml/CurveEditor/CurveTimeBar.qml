import QtQuick
import QtQuick.Controls

/**
 * CurveTimeBar displays the X axis of a CurveViewer with its playhead and fit interval.
 * It must have the same horizontal position and width as the viewer.
 *
 * Left drag moves the playhead, Shift+Left drag selects the fit interval,
 * double click on the interval clears it. Wheel zooms on X, Middle/Right drag pans on X.
 */

Rectangle {
    id: root

    clip: true
    color: palette.window

    /// CurveViewer driven by this bar
    property var viewer

    /// Mapping from X data value to pixel, written in QML so that bindings follow view changes
    function toPixel(x) {
        return (x - viewer.xMin) * viewer.width / (viewer.xMax - viewer.xMin)
    }

    function formatValue(x, step) {
        const decimals = Math.max(0, -Math.floor(Math.log10(step) + 1e-9))
        return x.toFixed(decimals)
    }

    readonly property real rangeX0: toPixel(Math.min(viewer.rangeStart, viewer.rangeEnd))
    readonly property real rangeX1: toPixel(Math.max(viewer.rangeStart, viewer.rangeEnd))

    // Fit interval
    Rectangle {
        visible: root.viewer.rangeEnabled
        x: root.rangeX0
        width: Math.max(1, root.rangeX1 - root.rangeX0)
        height: parent.height
        color: Qt.rgba(palette.highlight.r, palette.highlight.g, palette.highlight.b, 0.25)
        border.color: palette.highlight
    }

    // Graduations
    Repeater {
        model: root.viewer.xTicks

        delegate: Item {
            required property real position
            required property string label

            x: Math.floor(position)
            height: root.height

            Rectangle {
                anchors.bottom: parent.bottom
                width: 1
                height: 5
                color: palette.mid
            }

            Label {
                anchors.horizontalCenter: parent.left
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: -2
                text: parent.label
                font.pointSize: 8
                color: Qt.rgba(palette.text.r, palette.text.g, palette.text.b, 0.7)
            }
        }
    }

    // Playhead
    Rectangle {
        id: playheadBox

        readonly property real center: root.toPixel(root.viewer.playhead)

        visible: center >= -width / 2 && center <= root.width + width / 2
        x: Math.round(center - width / 2)
        anchors.verticalCenter: parent.verticalCenter
        width: playheadLabel.implicitWidth + 10
        height: parent.height - 6
        radius: 3
        color: palette.highlight

        Label {
            id: playheadLabel

            anchors.centerIn: parent
            text: root.formatValue(root.viewer.playhead, root.viewer.xTicks.step / 10)
            color: palette.highlightedText
            font.pointSize: 8
            font.bold: true
        }
    }

    // Bottom separator with the canvas
    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: palette.shadow
    }

    MouseArea {
        id: mouseArea

        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
        scrollGestureEnabled: false

        property bool selectingRange: false
        property bool panning: false
        property real rangeAnchor: 0
        property real lastX: 0

        function insideRange(px) {
            return root.viewer.rangeEnabled && px >= root.rangeX0 - 2 && px <= root.rangeX1 + 2
        }

        onPressed: function(mouse) {
            lastX = mouse.x
            if (mouse.button !== Qt.LeftButton) {
                panning = true
            } else if (mouse.modifiers & Qt.ShiftModifier) {
                selectingRange = true
                rangeAnchor = root.viewer.pixelToX(mouse.x)
            } else {
                root.viewer.playhead = root.viewer.pixelToX(mouse.x)
            }
        }

        onPositionChanged: function(mouse) {
            if (panning) {
                root.viewer.pan(mouse.x - lastX, 0)
            } else if (selectingRange) {
                const x = root.viewer.pixelToX(mouse.x)
                if (x !== rangeAnchor)
                    root.viewer.setRange(rangeAnchor, x)
            } else if (pressedButtons & Qt.LeftButton) {
                root.viewer.playhead = root.viewer.pixelToX(mouse.x)
            }
            lastX = mouse.x
        }

        onReleased: {
            selectingRange = false
            panning = false
        }
        onCanceled: {
            selectingRange = false
            panning = false
        }

        onDoubleClicked: function(mouse) {
            if (mouse.button === Qt.LeftButton && insideRange(mouse.x))
                root.viewer.rangeEnabled = false
        }

        onWheel: function(wheel) {
            const delta = wheel.angleDelta.y !== 0 ? wheel.angleDelta.y : wheel.angleDelta.x
            if (wheel.modifiers & Qt.ControlModifier) {
                root.viewer.pan(delta / 2, 0)
            } else {
                root.viewer.zoom(Math.pow(1.2, delta / 120), 1, wheel.x, 0)
            }
        }
    }
}
