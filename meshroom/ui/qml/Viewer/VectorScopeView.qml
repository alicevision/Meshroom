import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Controls 1.0

/**
 * VectorScopeView displays the vectorscope (chrominance plot) of the current image.
 * Pixel values are sampled from the FloatImageViewer via pixelValueAt() and
 * plotted in the CbCr (YCbCr BT.709) chrominance plane on a circular Canvas.
 * Reference target boxes are drawn at the standard 75% saturation positions
 * for the six primary/secondary colours.
 */

FloatingPane {
    id: root

    // The AliceVision FloatImageViewer item to sample pixels from
    property var floatImageViewer: null

    width: 220
    height: 240
    clip: true
    padding: 4

    // Prevent mouse/wheel events from passing through to the image below
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onWheel: function(wheel) { wheel.accepted = true }
    }

    // Sampled pixel data: each entry has { cb, cr, r, g, b }
    property var _scopeData: []
    property bool _dataReady: false

    function computeScope() {
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

                // Convert to CbCr (YCbCr BT.709 full range)
                // Cb = -0.1146*R - 0.3854*G + 0.5*B   range: [-0.5, +0.5]
                // Cr =  0.5*R    - 0.4542*G - 0.0458*B range: [-0.5, +0.5]
                var cb = -0.1146 * r - 0.3854 * g + 0.5 * b
                var cr =  0.5    * r - 0.4542 * g - 0.0458 * b

                newData.push({ cb: cb, cr: cr, r: r, g: g, b: b })
            }
        }

        _scopeData = newData
        _dataReady = true
        scopeCanvas.requestPaint()
    }

    // Recompute when the viewer item is replaced
    onFloatImageViewerChanged: computeScope()

    // Recompute when the panel becomes visible (image may already be loaded)
    onVisibleChanged: {
        if (visible)
            computeScope()
    }

    // Recompute when the image finishes loading
    Connections {
        target: root.floatImageViewer
        function onImageStatusChanged() {
            if (root.floatImageViewer && root.floatImageViewer.imageStatus === Image.Ready)
                root.computeScope()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 2

        // Header row: label
        RowLayout {
            spacing: 0

            Label {
                text: "Vector Scope"
                font.bold: true
                font.pointSize: 8
                leftPadding: 2
            }

            Item { Layout.fillWidth: true }
        }

        // Canvas for drawing the vectorscope
        Canvas {
            id: scopeCanvas
            Layout.fillWidth: true
            Layout.fillHeight: true

            onPaint: {
                var ctx = getContext("2d")
                var w = width
                var h = height
                ctx.clearRect(0, 0, w, h)

                var cx = w / 2
                var cy = h / 2
                var radius = Math.min(w, h) / 2 - 2

                // Map CbCr [-0.5, +0.5] to canvas coordinates.
                // x = cx + cb * scale,  y = cy - cr * scale  (flip Y for standard orientation)
                var scale = radius / 0.5

                // ── Background circle ─────────────────────────────────────
                ctx.beginPath()
                ctx.arc(cx, cy, radius, 0, 2 * Math.PI)
                ctx.fillStyle = "rgba(20, 20, 20, 0.85)"
                ctx.fill()
                ctx.strokeStyle = "rgba(100, 100, 100, 0.8)"
                ctx.lineWidth = 1
                ctx.stroke()

                // ── Graticule: concentric rings at 25 % / 50 % / 75 % saturation ────
                var graticuleRings = [0.25, 0.5, 0.75]
                ctx.strokeStyle = "rgba(80, 80, 80, 0.5)"
                ctx.lineWidth = 0.5
                ctx.setLineDash([3, 3])
                for (var pct of graticuleRings) {
                    ctx.beginPath()
                    ctx.arc(cx, cy, radius * pct, 0, 2 * Math.PI)
                    ctx.stroke()
                }
                ctx.setLineDash([])

                // ── Graticule: crosshair ──────────────────────────────────
                ctx.strokeStyle = "rgba(80, 80, 80, 0.5)"
                ctx.lineWidth = 0.5
                ctx.beginPath()
                ctx.moveTo(cx - radius, cy)
                ctx.lineTo(cx + radius, cy)
                ctx.stroke()
                ctx.beginPath()
                ctx.moveTo(cx, cy - radius)
                ctx.lineTo(cx, cy + radius)
                ctx.stroke()

                // ── 75 % saturation target boxes ─────────────────────────
                // Computed with: Cb = -0.1146*R -0.3854*G +0.5*B
                //                Cr =  0.5*R    -0.4542*G -0.0458*B
                // at 75 % saturation (channel value = 0.75, others = 0).
                // Example for Red: Cb = -0.1146*0.75 = -0.0860, Cr = 0.5*0.75 = 0.3750
                var targets = [
                    { cb: -0.0860, cr:  0.3750, color: "#ff4040", label: "R"  },
                    { cb: -0.3750, cr:  0.0344, color: "#e0e040", label: "Yl" },
                    { cb: -0.2891, cr: -0.3406, color: "#40c040", label: "G"  },
                    { cb:  0.0860, cr: -0.3750, color: "#40e0e0", label: "Cy" },
                    { cb:  0.3750, cr: -0.0344, color: "#4060ff", label: "B"  },
                    { cb:  0.2891, cr:  0.3406, color: "#c040c0", label: "Mg" },
                ]

                ctx.font = "7px sans-serif"
                ctx.lineWidth = 1
                for (var t of targets) {
                    var tx = cx + t.cb * scale
                    var ty = cy - t.cr * scale
                    ctx.strokeStyle = t.color
                    ctx.strokeRect(tx - 4, ty - 4, 8, 8)
                    ctx.fillStyle = t.color
                    ctx.fillText(t.label, tx + 6, ty + 3)
                }

                // ── Scatter plot ──────────────────────────────────────────
                if (!root._dataReady) return

                var data = root._scopeData
                for (var i = 0; i < data.length; i++) {
                    var pt = data[i]
                    var px = cx + pt.cb * scale
                    var py = cy - pt.cr * scale

                    // Clamp pixel colour to [0,1] and use it as the dot colour
                    var dr = Math.min(1, Math.max(0, pt.r))
                    var dg = Math.min(1, Math.max(0, pt.g))
                    var db = Math.min(1, Math.max(0, pt.b))

                    var ri = Math.round(dr * 255)
                    var gi = Math.round(dg * 255)
                    var bi = Math.round(db * 255)

                    ctx.fillStyle = "rgba(" + ri + "," + gi + "," + bi + ",0.6)"
                    ctx.fillRect(px - 0.5, py - 0.5, 1.5, 1.5)
                }
            }
        }
    }
}
