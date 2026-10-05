import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0
import CurveViewer 1.0 as CurveViewer

/**
 * CurveEditor displays curves like Blender's graph editor:
 * a list of curves on the left, an X axis bar with the playhead on top and the curves view.
 *
 * Mouse:
 *  - Wheel: zoom, Ctrl+Wheel: horizontal pan, Shift+Wheel: vertical pan
 *  - Middle/Right drag: pan, Ctrl+Middle/Right drag: scale X and Y independently
 *  - Left click on a curve: select it, Alt+Left drag: move the playhead
 *  - X axis bar: Left drag: move the playhead, Shift+Left drag: select the fit interval,
 *    double click on the interval: clear it
 *
 * Keyboard (only when the editor has the focus):
 *  - Home: fit all visible curves, F: fit the current curve
 *  - H: hide the current curve, Shift+H: hide the other curves, Alt+H: show all curves
 *  - Delete/X: remove the current curve
 *  - Alt+R: clear the fit interval
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

    /// Color bands drawn at the top of the curves,
    /// add bands with bands.addBand(name, xs, colors) or bands.addBandFromValues(name, xs, values[, gradient, min, max])
    property CurveViewer.CurveBandModel bands: CurveViewer.CurveBandModel {}

    readonly property alias viewer: canvas.viewer

    /// Height of the list header and of the X axis bar
    property real headerHeight: 26

    /// Extensions (with their leading dot, case insensitive) of the SfMData files that can be dropped on the editor
    property var acceptedExtensions: [".abc", ".sfm", ".usda"]

    function fitAll() {
        viewer.fitAll()
    }

    function removeCurrent() {
        if (viewer.currentIndex >= 0)
            model.removeCurve(viewer.currentIndex)
    }

    function hideOthers() {
        const current = viewer.currentIndex
        for (let row = 0; row < model.count; ++row) {
            if (row !== current)
                model.setVisible(row, false)
        }
    }

    // Shortcuts are handled here instead of using Shortcut items:
    // Shortcut contexts are window wide, while these keys must only act when the editor has the focus.
    Keys.onPressed: function(event) {
        const alt = event.modifiers & Qt.AltModifier
        const shift = event.modifiers & Qt.ShiftModifier
        const ctrl = event.modifiers & Qt.ControlModifier
        if (ctrl) {
            return
        }

        event.accepted = true
        if (event.key === Qt.Key_Home) {
            fitAll()
        } else if (event.key === Qt.Key_F && !alt && !shift) {
            if (viewer.currentIndex >= 0)
                viewer.fitCurve(viewer.currentIndex)
            else
                fitAll()
        } else if (event.key === Qt.Key_H && alt) {
            model.setAllVisible(true)
        } else if (event.key === Qt.Key_H && shift) {
            hideOthers()
        } else if (event.key === Qt.Key_H) {
            if (viewer.currentIndex >= 0)
                model.setVisible(viewer.currentIndex, false)
        } else if ((event.key === Qt.Key_Delete || event.key === Qt.Key_X) && !alt && !shift) {
            removeCurrent()
        } else if (event.key === Qt.Key_R && alt) {
            viewer.rangeEnabled = false
        } else {
            event.accepted = false
        }
    }

    Rectangle {
        anchors.fill: parent
        color: palette.window
    }

    MSplitView {
        anchors.fill: parent

        CurveList {
            SplitView.preferredWidth: 280
            SplitView.minimumWidth: 160
            model: root.model
            viewer: root.viewer
            headerHeight: root.headerHeight
        }

        ColumnLayout {
            SplitView.fillWidth: true
            SplitView.minimumWidth: 100
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
                bands: root.bands
            }
        }
    }

    // Load the camera trajectories of the dropped SfMData files
    DropArea {
        id: dropArea

        anchors.fill: parent
        enabled: root.acceptedExtensions.length > 0

        function acceptedUrls(urls) {
            return urls.filter(url => root.model.isAcceptedFile(url, root.acceptedExtensions))
        }

        onEntered: function(drag) {
            drag.accepted = drag.hasUrls && acceptedUrls(drag.urls).length > 0
        }

        onDropped: function(drop) {
            const urls = acceptedUrls(drop.urls)
            if (urls.length === 0)
                return
            drop.accept()
            for (const url of urls)
                root.model.loadFromSfmData(url)
            root.fitAll()
        }

        Rectangle {
            anchors.fill: parent
            visible: dropArea.containsDrag
            color: Qt.rgba(palette.highlight.r, palette.highlight.g, palette.highlight.b, 0.15)
            border.color: palette.highlight
            border.width: 2
        }
    }

    // Give the focus to the editor on any click inside it, without consuming the event
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        scrollGestureEnabled: false
        onPressed: function(mouse) {
            root.forceActiveFocus()
            mouse.accepted = false
        }
    }
}
