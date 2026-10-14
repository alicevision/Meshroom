import QtQuick

import CurveViewer 1.0 as CurveViewer

/**
 * CurveEditor displays curves like Blender's graph editor.
 *
 * Mouse:
 *  - Wheel: zoom, Ctrl+Wheel: horizontal pan, Shift+Wheel: vertical pan
 *  - Middle/Right drag: pan, Ctrl+Middle/Right drag: scale X and Y independently
 *  - Left click on a curve: select it, Alt+Left drag: move the playhead
 *
 * Requires the curveViewer plugin from QtAliceVision.
 */

FocusScope {
    id: root

    clip: true

    /// Curves to display, add curves with model.addCurve(name, xs, ys[, color])
    property CurveViewer.CurveModel model: CurveViewer.CurveModel {}

    readonly property alias viewer: canvas.viewer

    Rectangle {
        anchors.fill: parent
        color: palette.window
    }

    CurveCanvas {
        id: canvas

        anchors.fill: parent
        model: root.model
    }
}
