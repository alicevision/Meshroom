import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import MaterialIcons 2.2

/**
 * Editor of a set of curves stored as JSON {name: [[x, y], ...]} in a StringParam with the "curves"
 * semantic (see meshroom/core/curves.py: monotone cubic curves through their points).
 *
 * - the buttons above choose the edited curve (the others are drawn faintly);
 * - click to add a point (and drag it), drag a point, double-click a point to remove it;
 * - Ctrl + wheel (in the attribute editor; the wheel alone scrolls it) or wheel (in the curve window):
 *   zoom around the cursor (+ Shift: horizontally only, + Alt: vertically only); middle drag or
 *   Alt + drag: pan; "fit" button: show all the points again;
 * - the "open in window" button shows the editor in its own resizable window (with a full screen button).
 * Each press and release is one undoable change.
 */
ColumnLayout {
    id: root

    required property var attribute
    property bool editable: true
    // Editor shown in its own window: the plot fills the height, no pop-out button
    property bool inWindow: false

    readonly property var node: attribute.node
    readonly property var curves: {
        try {
            var parsed = JSON.parse(attribute.value || "{}")
            return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {}
        } catch (e) {
            return {}
        }
    }
    readonly property var names: Object.keys(curves)
    property string activeName: ""
    // Height of the plot (drag the handle under it to resize), remembered while the editor exists
    property real plotHeight: 200
    // Index of the selected point of the active curve (edited with the x / y fields), -1 if none
    property int selectedIndex: -1
    readonly property var selectedPoint: {
        var points = sortedPoints(active)
        return selectedIndex >= 0 && selectedIndex < points.length ? points[selectedIndex] : null
    }
    readonly property string active: names.indexOf(activeName) >= 0 ? activeName : (names.length > 0 ? names[0] : "")
    readonly property var colors: ({
        "master": "#E0E0E0", "red": "#E57373", "green": "#81C784", "blue": "#64B5F6", "alpha": "#9E9E9E",
        "hue": "#CE93D8", "saturation": "#FFB74D", "value": "#F5F5F5"
    })
    // View range {x0, x1, y0, y1}: zoomed / panned by the user, else fitted to the points; frozen while dragging
    property var view: null
    property var frozenBounds: null
    readonly property var bounds: view ? view : (frozenBounds ? frozenBounds : computeBounds())

    spacing: 2

    function copy(value) { return JSON.parse(JSON.stringify(value)) }

    function computeBounds() {
        // The unit square, extended to the points
        var x0 = 0, y0 = 0, x1 = 1, y1 = 1
        names.forEach(function(name) {
            (curves[name] || []).forEach(function(p) {
                x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0])
                y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1])
            })
        })
        var padX = (x1 - x0) * 0.05, padY = (y1 - y0) * 0.05
        return { "x0": x0 - padX, "x1": x1 + padX, "y0": y0 - padY, "y1": y1 + padY }
    }

    // Zoom by `factor` (< 1: in) around the curve point (cx, cy)
    function zoom(factor, cx, cy, horizontal, vertical) {
        var b = bounds
        var x0 = b.x0, x1 = b.x1, y0 = b.y0, y1 = b.y1
        if (horizontal) {
            x0 = cx + (x0 - cx) * factor
            x1 = cx + (x1 - cx) * factor
        }
        if (vertical) {
            y0 = cy + (y0 - cy) * factor
            y1 = cy + (y1 - cy) * factor
        }
        if (x1 - x0 < 1e-4 || y1 - y0 < 1e-4 || x1 - x0 > 1e7 || y1 - y0 > 1e7)
            return
        view = { "x0": x0, "x1": x1, "y0": y0, "y1": y1 }
    }

    function pan(dxCurve, dyCurve) {
        var b = bounds
        view = { "x0": b.x0 - dxCurve, "x1": b.x1 - dxCurve, "y0": b.y0 - dyCurve, "y1": b.y1 - dyCurve }
    }

    function toScreenX(x) { return (x - bounds.x0) / (bounds.x1 - bounds.x0) * plot.width }
    function toScreenY(y) { return plot.height - (y - bounds.y0) / (bounds.y1 - bounds.y0) * plot.height }
    function toCurveX(px) { return bounds.x0 + px / plot.width * (bounds.x1 - bounds.x0) }
    function toCurveY(py) { return bounds.y0 + (plot.height - py) / plot.height * (bounds.y1 - bounds.y0) }

    function sortedPoints(name) {
        return copy(curves[name] || []).sort(function(a, b) { return a[0] - b[0] })
    }

    function begin() { _currentScene.beginInteractiveEdit(root.attribute) }
    function apply(newCurves) { _currentScene.setValueInteractively(root.attribute, JSON.stringify(newCurves)) }
    function end() { _currentScene.endInteractiveEdit(root.attribute) }

    onCurvesChanged: plot.requestPaint()
    onActiveChanged: {
        selectedIndex = -1
        plot.requestPaint()
    }
    onSelectedIndexChanged: plot.requestPaint()

    // Set the selected point (x / y fields): kept between its neighbors
    function setSelectedPoint(x, y) {
        var points = sortedPoints(active)
        if (selectedIndex < 0 || selectedIndex >= points.length || !isFinite(x) || !isFinite(y))
            return
        var minX = selectedIndex > 0 ? points[selectedIndex - 1][0] + 1e-3 : -Infinity
        var maxX = selectedIndex < points.length - 1 ? points[selectedIndex + 1][0] - 1e-3 : Infinity
        points[selectedIndex] = [Math.max(minX, Math.min(maxX, x)), y]
        var newCurves = copy(curves)
        newCurves[active] = points
        begin()
        apply(newCurves)
        end()
    }
    onBoundsChanged: plot.requestPaint()

    // Curve choice
    RowLayout {
        Layout.fillWidth: true
        spacing: 2
        Repeater {
            model: root.names
            ToolButton {
                required property string modelData
                text: modelData
                checked: root.active === modelData
                font.pointSize: 8
                padding: 3
                contentItem: Label {
                    text: parent.text
                    font: parent.font
                    color: root.colors[parent.modelData] || "white"
                    opacity: parent.checked ? 1.0 : 0.6
                    horizontalAlignment: Text.AlignHCenter
                }
                onClicked: root.activeName = modelData
            }
        }
        Item { Layout.fillWidth: true }
        MaterialToolButton {
            text: MaterialIcons.fit_screen
            font.pointSize: 9
            padding: 2
            enabled: root.view !== null
            ToolTip.text: "Fit the view to the curves.\nZoom: Ctrl + wheel (wheel in the curve window), Shift: horizontally, " +
                          "Alt: vertically. Pan: middle drag or Alt + drag."
            onClicked: root.view = null
        }
        MaterialToolButton {
            visible: !root.inWindow
            text: MaterialIcons.open_in_new
            font.pointSize: 9
            padding: 2
            checked: curveWindowLoader.active
            ToolTip.text: curveWindowLoader.active ? "Close the curve window" : "Open the curves in a window"
            onClicked: curveWindowLoader.active = !curveWindowLoader.active
        }
        MaterialToolButton {
            visible: root.inWindow
            text: root.Window.window && root.Window.window.visibility === Window.FullScreen ? MaterialIcons.fullscreen_exit
                                                                                         : MaterialIcons.fullscreen
            font.pointSize: 9
            padding: 2
            ToolTip.text: "Full screen"
            onClicked: {
                var w = root.Window.window
                if (w)
                    w.visibility = w.visibility === Window.FullScreen ? Window.Windowed : Window.FullScreen
            }
        }
        MaterialToolButton {
            text: MaterialIcons.restart_alt
            font.pointSize: 9
            padding: 2
            enabled: root.editable && root.active !== ""
            ToolTip.text: "Reset the " + root.active + " curve"
            onClicked: {
                var newCurves = root.copy(root.curves)
                newCurves[root.active] = [[0, 0], [1, 1]]
                root.begin()
                root.apply(newCurves)
                root.end()
            }
        }
    }

    // Selected point, edited by value
    RowLayout {
        Layout.fillWidth: true
        spacing: 4
        Label {
            text: "x"
            font.pointSize: 8
            opacity: 0.7
        }
        TextField {
            id: pointXField
            Layout.fillWidth: true
            font.pointSize: 8
            enabled: root.editable && root.selectedPoint !== null
            text: root.selectedPoint ? String(Math.round(root.selectedPoint[0] * 10000) / 10000) : ""
            validator: DoubleValidator { locale: 'C' }
            selectByMouse: true
            onEditingFinished: root.setSelectedPoint(Number(text), root.selectedPoint ? root.selectedPoint[1] : NaN)
        }
        Label {
            text: "y"
            font.pointSize: 8
            opacity: 0.7
        }
        TextField {
            id: pointYField
            Layout.fillWidth: true
            font.pointSize: 8
            enabled: root.editable && root.selectedPoint !== null
            text: root.selectedPoint ? String(Math.round(root.selectedPoint[1] * 10000) / 10000) : ""
            validator: DoubleValidator { locale: 'C' }
            selectByMouse: true
            onEditingFinished: root.setSelectedPoint(root.selectedPoint ? root.selectedPoint[0] : NaN, Number(text))
        }
        Label {
            visible: root.selectedPoint === null
            text: "(select a point)"
            font.pointSize: 7
            opacity: 0.5
        }
    }

    // Plot
    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: root.inWindow
        Layout.preferredHeight: root.inWindow ? -1 : root.plotHeight
        color: Qt.rgba(0, 0, 0, 0.25)
        border.color: Qt.rgba(1, 1, 1, 0.1)

        Canvas {
            id: plot
            anchors.fill: parent
            anchors.margins: 1
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                if (width <= 0 || height <= 0)
                    return
                var b = root.bounds
                // Grid: 0.25 steps, or a power of 10 giving a few lines on a larger range
                ctx.strokeStyle = Qt.rgba(1, 1, 1, 0.07)
                ctx.lineWidth = 1
                var span = Math.max(b.x1 - b.x0, b.y1 - b.y0)
                var step = span <= 2 ? 0.25 : Math.pow(10, Math.floor(Math.log10(span / 2)))
                for (var gx = Math.ceil(b.x0 / step) * step; gx <= b.x1; gx += step) {
                    ctx.beginPath(); ctx.moveTo(root.toScreenX(gx), 0); ctx.lineTo(root.toScreenX(gx), height); ctx.stroke()
                }
                for (var gy = Math.ceil(b.y0 / step) * step; gy <= b.y1; gy += step) {
                    ctx.beginPath(); ctx.moveTo(0, root.toScreenY(gy)); ctx.lineTo(width, root.toScreenY(gy)); ctx.stroke()
                }
                // Identity
                ctx.strokeStyle = Qt.rgba(1, 1, 1, 0.15)
                ctx.setLineDash([3, 3])
                ctx.beginPath()
                ctx.moveTo(root.toScreenX(b.x0), root.toScreenY(b.x0))
                ctx.lineTo(root.toScreenX(b.x1), root.toScreenY(b.x1))
                ctx.stroke()
                ctx.setLineDash([])

                // Curves: the active one last, on top
                var order = root.names.filter(function(n) { return n !== root.active })
                if (root.active)
                    order.push(root.active)
                var count = Math.max(2, Math.round(width / 2))
                order.forEach(function(name) {
                    var isActive = name === root.active
                    var values = _currentScene.sampleCurve(root.sortedPoints(name), b.x0, b.x1, count)
                    ctx.strokeStyle = root.colors[name] || "white"
                    ctx.globalAlpha = isActive ? 1.0 : 0.35
                    ctx.lineWidth = isActive ? 1.6 : 1
                    ctx.beginPath()
                    for (var i = 0; i < values.length; i++) {
                        var px = i / (values.length - 1) * width
                        var py = root.toScreenY(values[i])
                        if (i === 0) ctx.moveTo(px, py)
                        else ctx.lineTo(px, py)
                    }
                    ctx.stroke()
                })
                ctx.globalAlpha = 1.0
                // Points of the active curve
                root.sortedPoints(root.active).forEach(function(p, index) {
                    ctx.fillStyle = index === plotMouse.dragged || index === root.selectedIndex ? "white" : (root.colors[root.active] || "white")
                    ctx.fillRect(root.toScreenX(p[0]) - 3.5, root.toScreenY(p[1]) - 3.5, 7, 7)
                })
            }
        }

        MouseArea {
            id: plotMouse
            anchors.fill: plot
            enabled: root.active !== ""
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
            // Vertical drags move the points, not the attribute list around
            preventStealing: true
            property int dragged: -1
            property var points: []
            // Panning (middle button or Alt + left): last position
            property bool panning: false
            property real lastX
            property real lastY
            property bool editing: false

            onWheel: function(wheel) {
                // In the attribute editor, the wheel alone scrolls the editor: Ctrl + wheel zooms
                if (!root.inWindow && !(wheel.modifiers & Qt.ControlModifier)) {
                    wheel.accepted = false
                    return
                }
                var delta = wheel.angleDelta.y !== 0 ? wheel.angleDelta.y : wheel.angleDelta.x
                var factor = delta > 0 ? 0.8 : 1.25
                var horizontal = !(wheel.modifiers & Qt.AltModifier)
                var vertical = !(wheel.modifiers & Qt.ShiftModifier)
                root.zoom(factor, root.toCurveX(wheel.x), root.toCurveY(wheel.y), horizontal, vertical)
            }

            function hit(mx, my) {
                var points = root.sortedPoints(root.active)
                for (var i = 0; i < points.length; i++) {
                    if (Math.abs(root.toScreenX(points[i][0]) - mx) < 6 && Math.abs(root.toScreenY(points[i][1]) - my) < 6)
                        return i
                }
                return -1
            }

            onPressed: function(mouse) {
                panning = mouse.button === Qt.MiddleButton || (mouse.modifiers & Qt.AltModifier)
                editing = !panning && root.editable
                if (panning) {
                    lastX = mouse.x
                    lastY = mouse.y
                    return
                }
                if (!editing)
                    return
                root.frozenBounds = root.computeBounds()
                points = root.sortedPoints(root.active)
                dragged = hit(mouse.x, mouse.y)
                root.selectedIndex = dragged
                root.begin()
                if (dragged < 0) {
                    // New point, then dragged
                    var x = root.toCurveX(mouse.x), y = root.toCurveY(mouse.y)
                    points = points.filter(function(p) { return Math.abs(p[0] - x) > 1e-6 })
                    points.push([x, y])
                    points.sort(function(a, b) { return a[0] - b[0] })
                    dragged = points.findIndex(function(p) { return p[0] === x })
                    root.selectedIndex = dragged
                    var newCurves = root.copy(root.curves)
                    newCurves[root.active] = points
                    root.apply(newCurves)
                }
            }
            onPositionChanged: function(mouse) {
                if (pressed && panning) {
                    var b = root.bounds
                    root.pan((mouse.x - lastX) / plot.width * (b.x1 - b.x0), -(mouse.y - lastY) / plot.height * (b.y1 - b.y0))
                    lastX = mouse.x
                    lastY = mouse.y
                    return
                }
                if (!pressed || !editing || dragged < 0)
                    return
                var x = root.toCurveX(mouse.x), y = root.toCurveY(mouse.y)
                // Keep the x order: between the neighbors
                var minX = dragged > 0 ? points[dragged - 1][0] + 1e-3 : -Infinity
                var maxX = dragged < points.length - 1 ? points[dragged + 1][0] - 1e-3 : Infinity
                x = Math.max(minX, Math.min(maxX, x))
                points[dragged] = [x, y]
                var newCurves = root.copy(root.curves)
                newCurves[root.active] = points
                root.apply(newCurves)
            }
            onReleased: {
                panning = false
                if (!editing)
                    return
                editing = false
                dragged = -1
                root.end()
                root.frozenBounds = null
            }
            onCanceled: {
                panning = false
                if (!editing)
                    return
                editing = false
                dragged = -1
                root.end()
                root.frozenBounds = null
            }
            onDoubleClicked: function(mouse) {
                if (!root.editable || mouse.button !== Qt.LeftButton || (mouse.modifiers & Qt.AltModifier))
                    return
                var index = hit(mouse.x, mouse.y)
                if (index < 0)
                    return
                var newCurves = root.copy(root.curves)
                var remaining = root.sortedPoints(root.active)
                remaining.splice(index, 1)
                root.selectedIndex = -1
                newCurves[root.active] = remaining
                root.begin()
                root.apply(newCurves)
                root.end()
            }
        }

        // Resize handle: drag to make the plot taller or shorter
        Rectangle {
            visible: !root.inWindow
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 6
            color: resizeMouse.containsMouse || resizeMouse.pressed ? Qt.rgba(1, 1, 1, 0.25) : Qt.rgba(1, 1, 1, 0.06)
            MouseArea {
                id: resizeMouse
                anchors.fill: parent
                hoverEnabled: true
                preventStealing: true
                cursorShape: Qt.SizeVerCursor
                property real startY
                property real startHeight
                onPressed: function(mouse) {
                    startY = mapToItem(null, mouse.x, mouse.y).y
                    startHeight = root.plotHeight
                }
                onPositionChanged: function(mouse) {
                    if (pressed)
                        root.plotHeight = Math.max(100, Math.min(1200, startHeight + mapToItem(null, mouse.x, mouse.y).y - startY))
                }
            }
        }

        // Coordinates under the cursor
        Label {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 3
            visible: plotMouse.containsMouse
            font.pointSize: 7
            opacity: 0.7
            text: {
                return root.toCurveX(plotMouse.mouseX).toFixed(3) + ", " + root.toCurveY(plotMouse.mouseY).toFixed(3)
            }
        }
    }

    // The curves in their own window (same attribute: both editors stay in sync)
    Loader {
        id: curveWindowLoader
        active: false
        sourceComponent: Window {
            id: curveWindow
            title: root.attribute.node.label + " - " + root.attribute.label
            width: 900
            height: 700
            minimumWidth: 300
            minimumHeight: 240
            visible: true
            onClosing: curveWindowLoader.active = false

            Pane {
                anchors.fill: parent
                padding: 6
                Loader {
                    anchors.fill: parent
                    Component.onCompleted: setSource("CurveEditor.qml", {
                        "attribute": root.attribute,
                        "editable": Qt.binding(function() { return root.editable }),
                        "inWindow": true
                    })
                }
            }
            Shortcut {
                sequence: "Escape"
                enabled: curveWindow.visibility === Window.FullScreen
                onActivated: curveWindow.visibility = Window.Windowed
            }
        }
    }
}
