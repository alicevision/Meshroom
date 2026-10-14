import QtQuick
import QtQuick.Layouts

import CurveViewer 1.0 as CurveViewer

/**
 * CurveEditor displays curves like Blender's graph editor:
 * an X axis bar with the playhead on top of the curves view.
 *
 * Mouse:
 *  - Wheel: zoom, Ctrl+Wheel: horizontal pan, Shift+Wheel: vertical pan
 *  - Middle/Right drag: pan, Ctrl+Middle/Right drag: scale X and Y independently
 *  - Left click on a curve: select it, Alt+Left drag: move the playhead
 *  - X axis bar: Left drag: move the playhead, Shift+Left drag: select the fit interval,
 *    double click on the interval: clear it
 *
 * Fit computations are restricted to the fit interval when it is enabled.
 *
 * Requires the curveViewer plugin from QtAliceVision.
 */

FocusScope {
    id: root

    clip: true

    /// Curves to display, add curves with model.addCurve(name, xs, ys[, color])
    property CurveViewer.CurveModel model: CurveViewer.CurveModel {}

    readonly property alias viewer: canvas.viewer

    /// Height of the X axis bar
    property real headerHeight: 26

    Rectangle {
        anchors.fill: parent
        color: palette.window
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        CurveTimeBar {
            Layout.fillWidth: true
            Layout.preferredHeight: root.headerHeight
            viewer: root.viewer
        }

        CurveCanvas {
            id: canvas

            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.model
        }
    }
}
