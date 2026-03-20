import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

/**
 * HistogramView displays the RGB/Luminance histogram of the current image.
 * Pixel values are sampled from the FloatImageViewer via pixelValueAt() and
 * accumulated into 256 bins per channel. The result is drawn on a Canvas.
 */

FloatingPane {
    id: root

    // The AliceVision FloatImageViewer item to sample pixels from
    property var floatImageViewer: null

    width: 280
    height: 140
    clip: true
    padding: 4

    // Prevent mouse/wheel events from passing through to the image below
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onWheel: function(wheel) { wheel.accepted = true }
    }

    readonly property int numBins: 256

    // Per-channel histogram data (arrays of numBins counts)
    property var _histR: []
    property var _histG: []
    property var _histB: []
    property var _histL: []
    property bool _histogramReady: false

    function computeHistogram() {
        _histogramReady = false

        if (!visible) return
        if (!floatImageViewer) return
        if (floatImageViewer.imageStatus !== Image.Ready) return

        var imgW = floatImageViewer.sourceSize.width
        var imgH = floatImageViewer.sourceSize.height
        if (imgW <= 0 || imgH <= 0) return

        var n = numBins
        var newR = new Array(n).fill(0)
        var newG = new Array(n).fill(0)
        var newB = new Array(n).fill(0)
        var newL = new Array(n).fill(0)

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

                // Clamp values to [0, 1] range and map to bin index
                var r = Math.min(n - 1, Math.max(0, Math.floor(px.x * n)))
                var g = Math.min(n - 1, Math.max(0, Math.floor(px.y * n)))
                var b = Math.min(n - 1, Math.max(0, Math.floor(px.z * n)))
                // Luminance using standard coefficients (Rec. 709)
                var lum = Math.min(n - 1, Math.max(0, Math.floor(
                    (0.2126 * px.x + 0.7152 * px.y + 0.0722 * px.z) * n
                )))

                newR[r]++
                newG[g]++
                newB[b]++
                newL[lum]++
            }
        }

        _histR = newR
        _histG = newG
        _histB = newB
        _histL = newL
        _histogramReady = true
        histCanvas.requestPaint()
    }

    // Recompute when the viewer item is replaced
    onFloatImageViewerChanged: computeHistogram()

    // Recompute when the panel becomes visible (image may already be loaded)
    onVisibleChanged: {
        if (visible)
            computeHistogram()
    }

    // Recompute when the image finishes loading
    Connections {
        target: root.floatImageViewer
        function onImageStatusChanged() {
            if (root.floatImageViewer && root.floatImageViewer.imageStatus === Image.Ready)
                root.computeHistogram()
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
                text: "Histogram"
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
                onCheckedChanged: histCanvas.requestPaint()
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
                onCheckedChanged: histCanvas.requestPaint()
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
                onCheckedChanged: histCanvas.requestPaint()
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
                onCheckedChanged: histCanvas.requestPaint()
                TapHandler {
                    acceptedModifiers: Qt.ControlModifier
                    onTapped: root.soloChannel(lBtn)
                }
                TapHandler {
                    acceptedModifiers: Qt.NoModifier
                    onTapped: lBtn.checked = !lBtn.checked
                }
            }
            ToolButton {
                id: logBtn
                text: "Log"
                font.pointSize: 7
                padding: 2
                checkable: true
                checked: false
                onCheckedChanged: histCanvas.requestPaint()
            }
        }

        // Canvas for drawing the histogram bars
        Canvas {
            id: histCanvas
            Layout.fillWidth: true
            Layout.fillHeight: true

            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)

                if (!root._histogramReady) return

                var n = root.numBins
                var hR = root._histR
                var hG = root._histG
                var hB = root._histB
                var hL = root._histL
                var useLog = logBtn.checked

                // Find the maximum count across all visible channels for normalization
                var maxVal = 1
                for (var i = 0; i < n; i++) {
                    if (rBtn.checked) maxVal = Math.max(maxVal, hR[i])
                    if (gBtn.checked) maxVal = Math.max(maxVal, hG[i])
                    if (bBtn.checked) maxVal = Math.max(maxVal, hB[i])
                    if (lBtn.checked) maxVal = Math.max(maxVal, hL[i])
                }

                var scale = useLog ? Math.log(maxVal + 1) : maxVal

                function barHeight(val) {
                    return (useLog ? Math.log(val + 1) : val) / scale * height
                }

                var barW = width / n

                function drawChannel(hist, color) {
                    ctx.fillStyle = color
                    for (var j = 0; j < n; j++) {
                        var bh = barHeight(hist[j])
                        if (bh > 0) {
                            ctx.fillRect(
                                Math.floor(j * barW),
                                Math.floor(height - bh),
                                Math.max(1, Math.ceil(barW)),
                                Math.ceil(bh)
                            )
                        }
                    }
                }

                // Draw channels back to front for better blending
                if (lBtn.checked) drawChannel(hL, "rgba(220, 220, 220, 0.5)")
                if (bBtn.checked) drawChannel(hB, "rgba(50, 100, 255, 0.6)")
                if (gBtn.checked) drawChannel(hG, "rgba(50, 200, 50, 0.6)")
                if (rBtn.checked) drawChannel(hR, "rgba(255, 80, 50, 0.6)")
            }
        }
    }
}
