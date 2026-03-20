import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Charts 1.0
import MaterialIcons 2.2
import Utils 1.0


Item {
    id: root

    implicitWidth: 500
    implicitHeight: 500

    /// Statistics source file
    property url source

    property var sourceModified: undefined
    property var jsonObject
    property real fileVersion: 0.0

    property int nbReads: 1
    property real deltaTime: 1

    property int nbCores: 0
    property int cpuFrequency: 0

    property int ramTotal
    property string ramLabel: "RAM: "

    property int maxDisplayLength: 500
    property int gpuTotalMemory
    property int gpuMaxAxis: 100
    property string gpuName

    property color textColor: Colors.sysPalette.text

    readonly property var colors: [
        "#f44336",
        "#e91e63",
        "#9c27b0",
        "#673ab7",
        "#3f51b5",
        "#2196f3",
        "#03a9f4",
        "#00bcd4",
        "#009688",
        "#4caf50",
        "#8bc34a",
        "#cddc39",
        "#ffeb3b",
        "#ffc107",
        "#ff9800",
        "#ff5722",
        "#b71c1c",
        "#880E4F",
        "#4A148C",
        "#311B92",
        "#1A237E",
        "#0D47A1",
        "#01579B",
        "#006064",
        "#004D40",
        "#1B5E20",
        "#33691E",
        "#827717",
        "#F57F17",
        "#FF6F00",
        "#E65100",
        "#BF360C"
    ]

    onSourceChanged: {
        sourceModified = undefined;
        resetCharts()
        readSourceFile()
    }

    function getPropertyWithDefault(prop, name, defaultValue) {
        if (prop.hasOwnProperty(name)) {
            return prop[name]
        }
        return defaultValue
    }

    Timer {
        id: reloadTimer
        interval: root.deltaTime * 60000; running: true; repeat: false
        onTriggered: readSourceFile()
    }

    function readSourceFile() {
        // Make sure we are trying to load a statistics file
        if (!Filepath.urlToString(source).endsWith("statistics"))
            return

        var xhr = new XMLHttpRequest
        xhr.open("GET", source)

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE && xhr.status == 200) {
                if (sourceModified === undefined || sourceModified < xhr.getResponseHeader("Last-Modified")) {
                    try {
                        root.jsonObject = JSON.parse(xhr.responseText)
                    } catch(exc) {
                        console.warning("Failed to parse statistics file: " + source)
                        root.jsonObject = {}
                        return
                    }
                    resetCharts()
                    sourceModified = xhr.getResponseHeader("Last-Modified")
                    root.createCharts()
                    reloadTimer.restart()
                }
            }
        }
        xhr.send()
    }

    function resetCharts() {
        root.fileVersion = 0.0
        root.gpuMaxAxis = 100
        cpuChart.removeAllSeries()
        ramChart.removeAllSeries()
        gpuChart.removeAllSeries()
    }

    function createCharts() {
        root.deltaTime = getPropertyWithDefault(jsonObject, "interval", 30) / 60.0;
        root.fileVersion = getPropertyWithDefault(jsonObject, "fileVersion", 0.0)
        initCpuChart()
        initRamChart()
        initGpuChart()
    }


/**************************
***         CPU         ***
**************************/

    function initCpuChart() {

        var categories = []
        var categoryCount = 0
        var category
        do {
            category = jsonObject.computer.curves["cpuUsage." + categoryCount]
            if (category !== undefined) {
                categories.push(category)
                categoryCount++
            }
        } while(category !== undefined)

        var nbCores = categories.length
        root.nbCores = nbCores

        root.cpuFrequency = getPropertyWithDefault(jsonObject.computer, "cpuFreq", -1)
        root.nbReads = categories[0].length - 1

        // Build and add one series per CPU core
        for (var j = 0; j < nbCores; j++) {
            var cat = categories[j]
            var corePoints = []
            if (cat.length === 1) {
                corePoints = [{ x: 0, y: cat[0] }, { x: root.deltaTime, y: cat[0] }]
            } else {
                var displayLength = Math.min(maxDisplayLength, cat.length)
                var step = cat.length / displayLength
                for (var k = 0; k < displayLength; k++) {
                    var idx = Math.floor(k * step)
                    corePoints.push({ x: idx * root.deltaTime, y: cat[idx] })
                }
            }
            cpuChart.addSeries("CPU" + j, colors[j % colors.length], corePoints)
        }

        // Compute and add the AVERAGE series
        var avgDisplayLength = Math.min(maxDisplayLength, categories[0].length)
        var avgStep = categories[0].length / avgDisplayLength
        var average = []
        for (var avgIdx = 0; avgIdx < avgDisplayLength; avgIdx++) {
            average.push(0)
        }

        for (var m = 0; m < categories.length; m++) {
            var displayLengthB = Math.min(maxDisplayLength, categories[m].length)
            var stepB = categories[m].length / displayLengthB
            for (var n = 0; n < displayLengthB; n++) {
                average[n] += categories[m][Math.floor(n * stepB)]
            }
        }

        var avgPoints = []
        for (var q = 0; q < average.length; q++) {
            average[q] = average[q] / categories.length
            avgPoints.push({ x: q * root.deltaTime * avgStep, y: average[q] })
        }
        cpuChart.addSeries("AVERAGE", colors[colors.length - 1], avgPoints)
    }

    function hideOtherCpu(index) {
        cpuChart.setAllSeriesVisible(false)
        cpuChart.setSeriesVisible(index, true)
    }


/**************************
***         RAM         ***
**************************/

    function initRamChart() {

        var ram = getPropertyWithDefault(jsonObject.computer.curves, "ramUsage", -1)

        root.ramTotal = getPropertyWithDefault(jsonObject.computer, "ramTotal", -1)
        root.ramLabel = "RAM: "
        if (root.ramTotal <= 0) {
            var maxRamPeak = 0
            for (var i = 0; i < ram.length; i++) {
                maxRamPeak = Math.max(maxRamPeak, ram[i])
            }
            root.ramTotal = maxRamPeak
            root.ramLabel = "RAM Max Peak: "
        }

        var ramPoints = []
        if (ram.length === 1) {
            // Create 2 entries if we have only one input value to create a segment that can be displayed
            ramPoints = [{ x: 0, y: ram[0] }, { x: root.deltaTime, y: ram[0] }]
        } else {
            var displayLength = Math.min(maxDisplayLength, ram.length)
            var step = ram.length / displayLength
            for (var ii = 0; ii < displayLength; ii++) {
                var i = Math.floor(ii * step)
                ramPoints.push({ x: i * root.deltaTime, y: ram[i] })
            }
        }
        ramChart.addSeries(root.ramLabel + root.ramTotal + "GB", colors[10], ramPoints)
    }


/**************************
***         GPU         ***
**************************/

    function initGpuChart() {
        root.gpuTotalMemory = getPropertyWithDefault(jsonObject.computer, "gpuMemoryTotal", 0)
        root.gpuName = getPropertyWithDefault(jsonObject.computer, "gpuName", "")

        var gpuUsedMemory = getPropertyWithDefault(jsonObject.computer.curves, "gpuMemoryUsed", 0)
        var gpuUsed = getPropertyWithDefault(jsonObject.computer.curves, "gpuUsed", 0)
        var gpuTemperature = getPropertyWithDefault(jsonObject.computer.curves, "gpuTemperature", 0)

        var gpuMemoryRatio = root.gpuTotalMemory > 0 ? (100 / root.gpuTotalMemory) : 1

        var gpuUsedPoints = []
        var gpuMemPoints  = []
        var gpuTempPoints = []

        if (gpuUsedMemory.length === 1) {
            gpuUsedPoints = [{ x: 0, y: gpuUsed[0] },
                             { x: root.deltaTime, y: gpuUsed[0] }]
            gpuMemPoints  = [{ x: 0, y: gpuUsedMemory[0] * gpuMemoryRatio },
                             { x: root.deltaTime, y: gpuUsedMemory[0] * gpuMemoryRatio }]
            gpuTempPoints = [{ x: 0, y: gpuTemperature[0] },
                             { x: root.deltaTime, y: gpuTemperature[0] }]
            root.gpuMaxAxis = Math.max(gpuMaxAxis, gpuTemperature[0])
        } else {
            var displayLength = Math.min(maxDisplayLength, gpuUsedMemory.length)
            var step = gpuUsedMemory.length / displayLength
            for (var ii = 0; ii < displayLength; ii++) {
                var i = Math.floor(ii * step)
                gpuUsedPoints.push({ x: i * root.deltaTime, y: gpuUsed[i] })
                gpuMemPoints.push({ x: i * root.deltaTime, y: gpuUsedMemory[i] * gpuMemoryRatio })
                gpuTempPoints.push({ x: i * root.deltaTime, y: gpuTemperature[i] })
                root.gpuMaxAxis = Math.max(gpuMaxAxis, gpuTemperature[i])
            }
        }

        gpuChart.addSeries("GPU", colors[0], gpuUsedPoints)
        gpuChart.addSeries("Memory", colors[5], gpuMemPoints)
        gpuChart.addSeries("Temperature", colors[15], gpuTempPoints)
    }


/**************************
***          UI         ***
**************************/

    ScrollView {
        height: root.height
        width: root.width
        ScrollBar.vertical.policy: ScrollBar.AlwaysOn

        ColumnLayout {
            width: root.width


/**************************
***       CPU UI        ***
**************************/

            Button {
                id: toggleCpuBtn
                Layout.fillWidth: true
                text: "Toggle CPU's"
                state: "closed"

                onClicked: state === "opened" ? state = "closed" : state = "opened"

                MaterialLabel {
                    text: MaterialIcons.arrow_drop_down
                    font.pointSize: 14
                    anchors.right: parent.right
                }

                states: [
                    State {
                        name: "opened"
                        PropertyChanges { target: cpuBtnContainer; visible: true }
                        PropertyChanges { target: toggleCpuBtn; down: true }
                    },
                    State {
                        name: "closed"
                        PropertyChanges { target: cpuBtnContainer; visible: false }
                        PropertyChanges { target: toggleCpuBtn; down: false }
                    }
                ]
            }

            Item {
                id: cpuBtnContainer

                Layout.fillWidth: true
                implicitHeight: childrenRect.height
                Layout.leftMargin: 25

                RowLayout {
                    width: parent.width
                    anchors.horizontalCenter: parent.horizontalCenter

                    ChartViewCheckBox {
                        id: allCPU
                        text: "ALL"
                        color: textColor
                        checkState: cpuLegend.buttonGroup.checkState
                        leftPadding: 0
                        onClicked: {
                            var _checked = checked
                            cpuChart.setAllSeriesVisible(_checked)
                        }
                    }

                    LineChartLegend {
                        id: cpuLegend
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        chartView: cpuChart
                    }
                }
            }

            LineChart {
                id: cpuChart

                Layout.fillWidth: true
                Layout.preferredHeight: width / 2

                textColor: root.textColor
                title: "CPU: " + root.nbCores + " cores, " + root.cpuFrequency + "MHz"
                xAxisTitle: "Minutes"
                yAxisTitle: "%"
                xMin: 0
                xMax: root.deltaTime * Math.max(1, root.nbReads)
                yMin: 0
                yMax: 100

                visible: (root.fileVersion > 0.0)
            }

/**************************
***       RAM UI        ***
**************************/

            LineChart {
                id: ramChart

                Layout.fillWidth: true
                Layout.preferredHeight: width / 2

                textColor: root.textColor
                title: root.ramLabel + root.ramTotal + "GB"
                xAxisTitle: "Minutes"
                yAxisTitle: "%"
                xMin: 0
                xMax: root.deltaTime * Math.max(1, root.nbReads)
                yMin: 0
                yMax: 100

                visible: (root.fileVersion > 0.0)
            }

/**************************
***       GPU UI        ***
**************************/

            LineChart {
                id: gpuChart

                Layout.fillWidth: true
                Layout.preferredHeight: width / 2

                textColor: root.textColor
                title: (root.gpuName || root.gpuTotalMemory) ? ("GPU: " + root.gpuName + ", " + root.gpuTotalMemory + "MB") : "No GPU"
                xAxisTitle: "Minutes"
                yAxisTitle: "%, °C"
                xMin: 0
                xMax: root.deltaTime * Math.max(1, root.nbReads)
                yMin: 0
                yMax: root.gpuMaxAxis

                visible: (root.fileVersion >= 2.0)
            }
        }
    }
}
