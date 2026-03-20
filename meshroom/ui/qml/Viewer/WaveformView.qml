import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

/**
 * WaveformView displays the waveform (signal level vs. horizontal image position) of
 * the current image.  Pixel values are sampled from the FloatImageViewer via
 * pixelValueAt() and plotted at their horizontal image position against their
 * per-channel intensity on a Canvas.  The result mirrors the layout of a classical
 * broadcast waveform monitor: the X axis represents image columns (left → right) and
 * the Y axis represents pixel intensity (bottom = 0, top = 1).
 */

FloatingPane {
    id: root

    // The AliceVision FloatImageViewer item to sample pixels from
    property var floatImageViewer: null

    width: 280
    height: 160
    clip: true
    padding: 4

    // Prevent mouse/wheel events from passing through to the image below
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onWheel: function(wheel) { wheel.accepted = true }
    }

    // Sampled pixel data: each entry has { xRatio, r, g, b, lum }
    property var _waveData: []
    property bool _dataReady: false

    function computeWaveform() {
        _dataReady = false

        if (!visible) return
        if (!floatImageViewer) return
        if (floatImageViewer.imageStatus !== Image.Ready) return

        var imgW = floatImageViewer.sourceSize.width
        var imgH = floatImageViewer.sourceSize.height
        if (imgW <= 0 || imgH <= 0) return

        var newData = []

        // Sample ~5000 pixels across the image.
        // Use separate step sizes per axis proportional to image dimensions
        // so that sampling remains spatially uniform on images with extreme aspect ratios.
        var targetSamples = 5000
        var stepsX = Math.max(1, Math.round(Math.sqrt(targetSamples * imgW / imgH)))
        var stepsY = Math.max(1, Math.round(Math.sqrt(targetSamples * imgH / imgW)))
        var stepX = Math.max(1, Math.floor(imgW / stepsX))
        var stepY = Math.max(1, Math.floor(imgH / stepsY))

        for (var y = 0; y < imgH; y += stepY) {
            for (var x = 0; x < imgW; x += stepX) {
                var px = floatImageViewer.pixelValueAt(x, y)
                if (!px) continue

                var r = px.x
                var g = px.y
                var b = px.z
                // Luminance using standard coefficients (Rec. 709)
                var lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

                newData.push({ xRatio: x / imgW, r: r, g: g, b: b, lum: lum })
            }
        }

        _waveData = newData
        _dataReady = true
        waveCanvas.requestPaint()
    }

    // Recompute when the viewer item is replaced
    onFloatImageViewerChanged: computeWaveform()

    // Recompute when the panel becomes visible (image may already be loaded)
    onVisibleChanged: {
        if (visible)
            computeWaveform()
    }

    // Recompute when the image finishes loading
    Connections {
        target: root.floatImageViewer
        function onImageStatusChanged() {
            if (root.floatImageViewer && root.floatImageViewer.imageStatus === Image.Ready)
                root.computeWaveform()
        }
    }

    // Activate solo mode for a channel button: turn it on and all others off.
    // Ctrl+click on any R/G/B/L button triggers this.
    function soloChannel(btn) {
        rBtn.checked = (btn === rBtn)
        gBtn.checked = (btn === gBtn)
        bBtn.checked = (btn === bBtn)
        lBtn.checked = (btn === lBtn)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 2

        // Header row: label and per-channel toggle buttons
        RowLayout {
            spacing: 0

            Label {
                text: "Waveform"
                font.bold: true
                font.pointSize: 8
                leftPadding: 2
            }

            Item { Layout.fillWidth: true }

            ToolButton {
                id: rBtn
                text: "R"
                font.pointSize: 7
                padding: 2
                checkable: false
                checked: true
                onCheckedChanged: waveCanvas.requestPaint()
                TapHandler {
                    acceptedModifiers: Qt.ControlModifier
                    onTapped: root.soloChannel(rBtn)
                }
                TapHandler {
                    acceptedModifiers: Qt.NoModifier
                    onTapped: rBtn.checked = !rBtn.checked
                }
            }
            ToolButton {
                id: gBtn
                text: "G"
                font.pointSize: 7
                padding: 2
                checkable: false
                checked: true
                onCheckedChanged: waveCanvas.requestPaint()
                TapHandler {
                    acceptedModifiers: Qt.ControlModifier
                    onTapped: root.soloChannel(gBtn)
                }
                TapHandler {
                    acceptedModifiers: Qt.NoModifier
                    onTapped: gBtn.checked = !gBtn.checked
                }
            }
            ToolButton {
                id: bBtn
                text: "B"
                font.pointSize: 7
                padding: 2
                checkable: false
                checked: true
                onCheckedChanged: waveCanvas.requestPaint()
                TapHandler {
                    acceptedModifiers: Qt.ControlModifier
                    onTapped: root.soloChannel(bBtn)
                }
                TapHandler {
                    acceptedModifiers: Qt.NoModifier
                    onTapped: bBtn.checked = !bBtn.checked
                }
            }
            ToolButton {
                id: lBtn
                text: "L"
                font.pointSize: 7
                padding: 2
                checkable: false
                checked: false
                onCheckedChanged: waveCanvas.requestPaint()
                TapHandler {
                    acceptedModifiers: Qt.ControlModifier
                    onTapped: root.soloChannel(lBtn)
                }
                TapHandler {
                    acceptedModifiers: Qt.NoModifier
                    onTapped: lBtn.checked = !lBtn.checked
                }
            }
        }

        // Canvas for drawing the waveform
        Canvas {
            id: waveCanvas
            Layout.fillWidth: true
            Layout.fillHeight: true

            onPaint: {
                var ctx = getContext("2d")
                var w = width
                var h = height
                ctx.clearRect(0, 0, w, h)

                // Background
                ctx.fillStyle = "rgba(20, 20, 20, 0.85)"
                ctx.fillRect(0, 0, w, h)

                // Graticule: horizontal dashed lines at 25 % / 50 % / 75 % intensity
                ctx.strokeStyle = "rgba(80, 80, 80, 0.5)"
                ctx.lineWidth = 0.5
                ctx.setLineDash([3, 3])
                for (var pct of [0.25, 0.5, 0.75]) {
                    var gy = Math.round(h - pct * h) + 0.5
                    ctx.beginPath()
                    ctx.moveTo(0, gy)
                    ctx.lineTo(w, gy)
                    ctx.stroke()
                }
                ctx.setLineDash([])

                if (!root._dataReady) return

                var data = root._waveData
                for (var i = 0; i < data.length; i++) {
                    var pt = data[i]
                    var posX = pt.xRatio * w - 0.5

                    // Draw channels back to front for better blending.
                    // Y axis: bottom = intensity 0, top = intensity 1
                    if (lBtn.checked) {
                        var ly = h - Math.min(1, Math.max(0, pt.lum)) * h - 0.5
                        ctx.fillStyle = "rgba(220, 220, 220, 0.35)"
                        ctx.fillRect(posX, ly, 1.5, 1.5)
                    }
                    if (bBtn.checked) {
                        var by = h - Math.min(1, Math.max(0, pt.b)) * h - 0.5
                        ctx.fillStyle = "rgba(50, 100, 255, 0.4)"
                        ctx.fillRect(posX, by, 1.5, 1.5)
                    }
                    if (gBtn.checked) {
                        var gy2 = h - Math.min(1, Math.max(0, pt.g)) * h - 0.5
                        ctx.fillStyle = "rgba(50, 200, 50, 0.4)"
                        ctx.fillRect(posX, gy2, 1.5, 1.5)
                    }
                    if (rBtn.checked) {
                        var ry = h - Math.min(1, Math.max(0, pt.r)) * h - 0.5
                        ctx.fillStyle = "rgba(255, 80, 50, 0.4)"
                        ctx.fillRect(posX, ry, 1.5, 1.5)
                    }
                }
            }
        }
    }
}
