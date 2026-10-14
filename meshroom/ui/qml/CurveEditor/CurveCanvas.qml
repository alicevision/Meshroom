import QtQuick
import QtQuick.Controls

import CurveViewer 1.0 as CurveViewer

/**
 * CurveCanvas draws the curves with their grid and Y axis graduations,
 * and implements the navigation in the view.
 */

Item {
    id: root

    clip: true

    property alias model: viewer.model
    property alias bands: viewer.bands
    readonly property alias viewer: viewer

    function withAlpha(c, alpha) {
        return Qt.rgba(c.r, c.g, c.b, alpha)
    }

    Rectangle {
        anchors.fill: parent
        color: palette.base
    }

    CurveViewer.CurveViewer {
        id: viewer

        anchors.fill: parent
        gridColor: root.withAlpha(palette.text, 0.07)
        playheadColor: palette.highlight
        rangeShadeColor: root.withAlpha(palette.shadow, 0.35)
    }

    // Y axis graduations
    Repeater {
        model: viewer.yTicks

        delegate: Label {
            required property real position
            required property string label

            x: 4
            y: position - height
            visible: y >= 0
            text: label
            color: root.withAlpha(palette.text, 0.6)
            font.pointSize: 8
        }
    }

    // Band names, on the left of each band
    Repeater {
        model: viewer.bands

        delegate: Label {
            required property int index
            required property string bandName
            required property bool bandVisible

            x: 4
            // Depend on bandsHeight to follow the bands stacking
            y: viewer.bandsHeight >= 0 ? viewer.bandY(index) + (viewer.bandHeight - height) / 2 : 0
            visible: bandVisible
            text: bandName
            color: palette.text
            style: Text.Outline
            styleColor: root.withAlpha(palette.base, 0.8)
            font.pointSize: 7
        }
    }

    MouseArea {
        id: mouseArea

        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
        scrollGestureEnabled: false
        cursorShape: dragMode === mouseArea.panMode ? Qt.ClosedHandCursor
                   : dragMode === mouseArea.scaleMode ? Qt.SizeAllCursor
                   : dragMode === mouseArea.scrubMode ? Qt.SizeHorCursor
                   : Qt.ArrowCursor

        readonly property int noMode: 0
        readonly property int panMode: 1
        readonly property int scaleMode: 2
        readonly property int scrubMode: 3

        property int dragMode: noMode
        property point pressPosition
        property point lastPosition

        onPressed: function(mouse) {
            pressPosition = Qt.point(mouse.x, mouse.y)
            lastPosition = pressPosition

            if (mouse.button === Qt.MiddleButton || mouse.button === Qt.RightButton) {
                dragMode = (mouse.modifiers & Qt.ControlModifier) ? scaleMode : panMode
            } else if (mouse.modifiers & Qt.AltModifier) {
                dragMode = scrubMode
                viewer.playhead = viewer.pixelToX(mouse.x)
            } else {
                dragMode = noMode
                // Curves are hidden under the bands
                if (viewer.bandAt(mouse.y) < 0)
                    viewer.currentIndex = viewer.curveAt(mouse.x, mouse.y, 6)
            }
        }

        onPositionChanged: function(mouse) {
            const dx = mouse.x - lastPosition.x
            const dy = mouse.y - lastPosition.y
            lastPosition = Qt.point(mouse.x, mouse.y)

            if (dragMode === panMode) {
                viewer.pan(dx, dy)
            } else if (dragMode === scaleMode) {
                // Dragging right/up zooms in on X/Y around the press position
                viewer.zoom(Math.exp(dx * 0.01), Math.exp(-dy * 0.01), pressPosition.x, pressPosition.y)
            } else if (dragMode === scrubMode) {
                viewer.playhead = viewer.pixelToX(mouse.x)
            }
        }

        onReleased: dragMode = noMode
        onCanceled: dragMode = noMode

        onDoubleClicked: function(mouse) {
            if (mouse.button === Qt.LeftButton && viewer.currentIndex >= 0)
                viewer.fitCurve(viewer.currentIndex)
        }

        onWheel: function(wheel) {
            const delta = wheel.angleDelta.y !== 0 ? wheel.angleDelta.y : wheel.angleDelta.x
            if (wheel.modifiers & Qt.ControlModifier) {
                viewer.pan(delta / 2, 0)
            } else if (wheel.modifiers & Qt.ShiftModifier) {
                viewer.pan(0, delta / 2)
            } else {
                const factor = Math.pow(1.2, delta / 120)
                viewer.zoom(factor, factor, wheel.x, wheel.y)
            }
        }
    }
}
