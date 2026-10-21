import QtQuick

/**
 * LineChart is a generic Canvas-based 2D line chart.
 *
 * It renders one or more named, colored line series on a plot area with
 * automatic axis scaling, grid lines, tick marks, and axis labels.
 * No QtCharts dependency is required.
 *
 * Usage:
 *   LineChart {
 *       title: "CPU Usage"
 *       xAxisTitle: "Minutes"
 *       yAxisTitle: "%"
 *       xMin: 0; xMax: 60
 *       yMin: 0; yMax: 100
 *       textColor: "white"
 *   }
 *
 *   // Add a series (returns the series index):
 *   var idx = chart.addSeries("CPU0", "#ff5722", [{x:0,y:10},{x:1,y:20}])
 *
 *   // Remove all series:
 *   chart.removeAllSeries()
 */

Item {
    id: root

    // ---- Chart labels -------------------------------------------------------

    /// Text shown centered above the plot area
    property string title: ""
    /// Label drawn along the X axis
    property string xAxisTitle: ""
    /// Label drawn along the Y axis (rotated 90°)
    property string yAxisTitle: ""

    // ---- Axis bounds --------------------------------------------------------

    property real xMin: 0
    property real xMax: 1
    property real yMin: 0
    property real yMax: 100

    // ---- Display settings ---------------------------------------------------

    property color textColor: palette.windowText
    /// Approximate number of tick marks on each axis
    property int suggestedTickCount: 5
    property int fontSize: 10

    // ---- Series API ---------------------------------------------------------

    /// Read-only number of series currently in the chart
    readonly property int count: _series.length

    /// Internal series storage – plain JS array of series descriptor objects:
    ///   { name, color, points:[{x,y}], visible, lineWidth }
    property var _series: []

    // Emitted when a series is added (index = position in _series)
    signal seriesAdded(int index)
    // Emitted when a series is removed (index = former position)
    signal seriesRemoved(int index)
    // Emitted whenever any series property (visibility, line width…) changes
    signal seriesChanged()

    /**
     * Add a series to the chart.
     * @param name      Display name for the legend
     * @param seriesColor CSS color string or QML color value
     * @param points    Array of {x, y} objects
     * @return          Index of the new series
     */
    function addSeries(name, seriesColor, points) {
        var s = {
            name: name,
            color: seriesColor,
            points: points || [],
            visible: true,
            lineWidth: 1.5
        }
        var arr = _series.slice()
        arr.push(s)
        _series = arr
        seriesAdded(_series.length - 1)
        canvas.requestPaint()
        return _series.length - 1
    }

    /// Remove all series from the chart
    function removeAllSeries() {
        var n = _series.length
        _series = []
        for (var i = 0; i < n; i++)
            seriesRemoved(i)
        seriesChanged()
        canvas.requestPaint()
    }

    /// Return the series descriptor object at index i
    function series(i) {
        return _series[i]
    }

    /// Show or hide the series at index i
    function setSeriesVisible(i, vis) {
        if (i < 0 || i >= _series.length) return
        var arr = _series.slice()
        arr[i] = _copyWith(arr[i], { visible: vis })
        _series = arr
        seriesChanged()
        canvas.requestPaint()
    }

    /// Set visible state for all series at once
    function setAllSeriesVisible(vis) {
        var arr = _series.map(function(s) { return _copyWith(s, { visible: vis }) })
        _series = arr
        seriesChanged()
        canvas.requestPaint()
    }

    /// Set the stroke width for the series at index i
    function setSeriesLineWidth(i, w) {
        if (i < 0 || i >= _series.length) return
        var arr = _series.slice()
        arr[i] = _copyWith(arr[i], { lineWidth: w })
        _series = arr
        canvas.requestPaint()
    }

    // ---- Helpers (private) --------------------------------------------------

    /// Shallow-copy an object, overriding keys from overrides
    function _copyWith(obj, overrides) {
        var result = {}
        for (var k in obj) result[k] = obj[k]
        for (var ok in overrides) result[ok] = overrides[ok]
        return result
    }

    /**
     * Compute a nice set of tick values for [minVal, maxVal].
     * Returns an array of evenly-spaced round numbers.
     */
    function _niceTicks(minVal, maxVal, n) {
        if (minVal >= maxVal) {
            maxVal = minVal + 1
        }
        var range = maxVal - minVal
        var rough = range / Math.max(n - 1, 1)
        var mag = Math.pow(10, Math.floor(Math.log(rough) / Math.LN10))
        var norm = rough / mag
        var step
        if      (norm < 1.5) step = mag
        else if (norm < 3.5) step = 2 * mag
        else if (norm < 7.5) step = 5 * mag
        else                 step = 10 * mag

        var start = Math.floor(minVal / step) * step
        start = parseFloat(start.toPrecision(10))

        var ticks = []
        var t = start
        var maxIter = (n + 2) * 3
        var iter = 0
        while (iter < maxIter) {
            iter++
            var rounded = parseFloat(t.toPrecision(10))
            if (rounded > maxVal + step * 0.01) break
            if (rounded >= minVal - step * 0.01)
                ticks.push(rounded)
            t += step
            t = parseFloat(t.toPrecision(10))
        }
        return ticks
    }

    /// Format a tick value compactly (no unnecessary trailing zeros)
    function _fmtLabel(val) {
        if (val === 0) return "0"
        var abs = Math.abs(val)
        if (abs >= 1000) return val.toFixed(0)
        if (abs >= 100)  return val.toFixed(0)
        if (abs >= 10)   return parseFloat(val.toFixed(1)).toString()
        return parseFloat(val.toFixed(2)).toString()
    }

    // ---- Visual -------------------------------------------------------------

    SystemPalette { id: palette }

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        onWidthChanged:  requestPaint()
        onHeightChanged: requestPaint()

        Connections {
            target: root
            function onXMinChanged()      { canvas.requestPaint() }
            function onXMaxChanged()      { canvas.requestPaint() }
            function onYMinChanged()      { canvas.requestPaint() }
            function onYMaxChanged()      { canvas.requestPaint() }
            function onTextColorChanged() { canvas.requestPaint() }
            function onTitleChanged()     { canvas.requestPaint() }
            function onXAxisTitleChanged(){ canvas.requestPaint() }
            function onYAxisTitleChanged(){ canvas.requestPaint() }
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)

            if (width <= 0 || height <= 0) return

            var w = width
            var h = height
            var fs = root.fontSize

            // ---- Compute axis ticks first (to measure Y label width) --------

            var xMin = root.xMin, xMax = root.xMax
            var yMin = root.yMin, yMax = root.yMax
            if (xMax <= xMin) xMax = xMin + 1
            if (yMax <= yMin) yMax = yMin + 1

            var yTicks = root._niceTicks(yMin, yMax, root.suggestedTickCount)
            var xTicks = root._niceTicks(xMin, xMax, root.suggestedTickCount)

            ctx.font = fs + "px sans-serif"
            var maxYLabelW = 0
            for (var ti = 0; ti < yTicks.length; ti++) {
                var lw = ctx.measureText(root._fmtLabel(yTicks[ti])).width
                if (lw > maxYLabelW) maxYLabelW = lw
            }

            // ---- Layout margins ---------------------------------------------

            var hasTitle  = root.title.length > 0
            var hasXTitle = root.xAxisTitle.length > 0
            var hasYTitle = root.yAxisTitle.length > 0

            var marginLeft   = maxYLabelW + 14 + (hasYTitle ? fs + 6 : 0)
            var marginRight  = 10
            var marginTop    = hasTitle ? (fs + 2) * 2 + 4 : 10
            var marginBottom = fs + 10 + (hasXTitle ? fs + 6 : 0)

            var plotX = Math.floor(marginLeft)
            var plotY = Math.floor(marginTop)
            var plotW = Math.floor(w - marginLeft - marginRight)
            var plotH = Math.floor(h - marginTop - marginBottom)

            if (plotW < 10 || plotH < 10) return

            // ---- Color helpers ----------------------------------------------

            var tc = root.textColor
            function tcToCSS(alpha) {
                return "rgba(" + Math.round(tc.r*255) + "," + Math.round(tc.g*255) + "," + Math.round(tc.b*255) + "," + alpha + ")"
            }
            var tcCSS   = tcToCSS(Math.min(tc.a, 1))
            var gridCSS = tcToCSS(0.15)
            var axisCSS = tcToCSS(0.5)

            // ---- Coordinate mapping -----------------------------------------

            function mapX(x) { return plotX + (x - xMin) / (xMax - xMin) * plotW }
            function mapY(y) { return plotY + (1.0 - (y - yMin) / (yMax - yMin)) * plotH }

            // ---- Draw title -------------------------------------------------

            if (hasTitle) {
                ctx.font = "bold " + (fs + 2) + "px sans-serif"
                ctx.fillStyle = tcCSS
                ctx.textAlign = "center"
                ctx.textBaseline = "middle"
                ctx.fillText(root.title, w / 2, marginTop / 2)
            }

            // ---- Draw Y axis label (rotated) ---------------------------------

            if (hasYTitle) {
                ctx.save()
                ctx.font = fs + "px sans-serif"
                ctx.fillStyle = tcCSS
                ctx.textAlign = "center"
                ctx.textBaseline = "middle"
                ctx.translate(fs / 2 + 2, plotY + plotH / 2)
                ctx.rotate(-Math.PI / 2)
                ctx.fillText(root.yAxisTitle, 0, 0)
                ctx.restore()
            }

            // ---- Draw X axis label ------------------------------------------

            if (hasXTitle) {
                ctx.font = fs + "px sans-serif"
                ctx.fillStyle = tcCSS
                ctx.textAlign = "center"
                ctx.textBaseline = "bottom"
                ctx.fillText(root.xAxisTitle, plotX + plotW / 2, h - 2)
            }

            // ---- Draw horizontal grid lines (at Y ticks) --------------------

            ctx.strokeStyle = gridCSS
            ctx.lineWidth = 1
            for (var yi = 0; yi < yTicks.length; yi++) {
                var gy = mapY(yTicks[yi])
                if (gy < plotY - 0.5 || gy > plotY + plotH + 0.5) continue
                ctx.beginPath()
                ctx.moveTo(plotX, gy)
                ctx.lineTo(plotX + plotW, gy)
                ctx.stroke()
            }

            // ---- Draw vertical grid lines (at X ticks) ----------------------

            for (var xi = 0; xi < xTicks.length; xi++) {
                var gx = mapX(xTicks[xi])
                if (gx < plotX - 0.5 || gx > plotX + plotW + 0.5) continue
                ctx.beginPath()
                ctx.moveTo(gx, plotY)
                ctx.lineTo(gx, plotY + plotH)
                ctx.stroke()
            }

            // ---- Draw plot border -------------------------------------------

            ctx.strokeStyle = axisCSS
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.rect(plotX, plotY, plotW, plotH)
            ctx.stroke()

            // ---- Draw Y tick marks and labels --------------------------------

            ctx.font = fs + "px sans-serif"
            ctx.fillStyle = tcCSS
            ctx.strokeStyle = axisCSS
            ctx.lineWidth = 1

            for (var yk = 0; yk < yTicks.length; yk++) {
                var ty = mapY(yTicks[yk])
                if (ty < plotY - 0.5 || ty > plotY + plotH + 0.5) continue
                ctx.textAlign = "right"
                ctx.textBaseline = "middle"
                ctx.fillText(root._fmtLabel(yTicks[yk]), plotX - 6, ty)
                ctx.beginPath()
                ctx.moveTo(plotX - 4, ty)
                ctx.lineTo(plotX, ty)
                ctx.stroke()
            }

            // ---- Draw X tick marks and labels --------------------------------

            for (var xk = 0; xk < xTicks.length; xk++) {
                var tx = mapX(xTicks[xk])
                if (tx < plotX - 0.5 || tx > plotX + plotW + 0.5) continue
                ctx.textAlign = "center"
                ctx.textBaseline = "top"
                ctx.fillText(root._fmtLabel(xTicks[xk]), tx, plotY + plotH + 5)
                ctx.beginPath()
                ctx.moveTo(tx, plotY + plotH)
                ctx.lineTo(tx, plotY + plotH + 4)
                ctx.stroke()
            }

            // ---- Draw series lines (clipped to plot area) -------------------

            ctx.save()
            ctx.beginPath()
            ctx.rect(plotX, plotY, plotW, plotH)
            ctx.clip()

            for (var si = 0; si < root._series.length; si++) {
                var s = root._series[si]
                if (!s.visible || !s.points || s.points.length === 0) continue

                ctx.strokeStyle = s.color.toString()
                ctx.lineWidth = s.lineWidth || 1.5
                ctx.lineJoin = "round"
                ctx.lineCap = "round"

                var pts = s.points
                ctx.beginPath()
                ctx.moveTo(mapX(pts[0].x), mapY(pts[0].y))
                for (var pi = 1; pi < pts.length; pi++) {
                    ctx.lineTo(mapX(pts[pi].x), mapY(pts[pi].y))
                }
                ctx.stroke()
            }

            ctx.restore()
        }
    }
}
