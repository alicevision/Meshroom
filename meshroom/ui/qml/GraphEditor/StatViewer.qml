import QtCharts
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
        cpuLegend.clear()
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

        root.nbReads = categories[0].length-1

        for (var j = 0; j < nbCores; j++) {
            var lineSerie = cpuChart.createSeries(ChartView.SeriesTypeLine, "CPU" + j, valueCpuX, valueCpuY)

            if (categories[j].length === 1) {
                lineSerie.append(0, categories[j][0])
                lineSerie.append(root.deltaTime, categories[j][0])
            } else {
                var displayLength = Math.min(maxDisplayLength, categories[j].length)
                var step = categories[j].length / displayLength
                for (var kk = 0; kk < displayLength; kk += step) {
                    var k = Math.floor(kk * step)
                    lineSerie.append(k * root.deltaTime, categories[j][k])
                }
            }
            lineSerie.color = colors[j % colors.length]
        }

        var averageLine = cpuChart.createSeries(ChartView.SeriesTypeLine, "AVERAGE", valueCpuX, valueCpuY)
        var average = []

        var displayLengthA = Math.min(maxDisplayLength, categories[0].length)
        var stepA = categories[0].length / displayLengthA
        for (var l = 0; l < displayLengthA; l += step) {
            average.push(0)
        }

        for (var m = 0; m < categories.length; m++) {
            var displayLengthB = Math.min(maxDisplayLength, categories[m].length)
            var stepB = categories[0].length / displayLengthB
            for (var nn = 0; nn < displayLengthB; nn++) {
                var n = Math.floor(nn * stepB)
                average[nn] += categories[m][n]
            }
        }

        for (var q = 0; q < average.length; q++) {
            average[q] = average[q] / (categories.length)
            averageLine.append(q * root.deltaTime * stepA, average[q])
        }

        averageLine.color = colors[colors.length - 1]
    }

    function hideOtherCpu(index) {
        for (var i = 0; i < cpuChart.count; i++) {
            cpuChart.series(i).visible = false
        }
        cpuChart.series(index).visible = true
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

        var ramSerie = ramChart.createSeries(ChartView.SeriesTypeLine, root.ramLabel + root.ramTotal + "GB", valueRamX, valueRamY)

        if (ram.length === 1) {
            // Create 2 entries if we have only one input value to create a segment that can be display
            ramSerie.append(0, ram[0])
            ramSerie.append(root.deltaTime, ram[0])
        } else {
            var displayLength = Math.min(maxDisplayLength, ram.length)
            var step = ram.length / displayLength
            for(var ii = 0; ii < displayLength; ii++) {
                var i = Math.floor(ii * step)
                ramSerie.append(i * root.deltaTime, ram[i])
            }
        }
        ramSerie.color = colors[10]
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

        var gpuUsedSerie = gpuChart.createSeries(ChartView.SeriesTypeLine, "GPU", valueGpuX, valueGpuY)
        var gpuUsedMemorySerie = gpuChart.createSeries(ChartView.SeriesTypeLine, "Memory", valueGpuX, valueGpuY)
        var gpuTemperatureSerie = gpuChart.createSeries(ChartView.SeriesTypeLine, "Temperature", valueGpuX, valueGpuY)

        var gpuMemoryRatio = root.gpuTotalMemory > 0 ? (100 / root.gpuTotalMemory) : 1

        if (gpuUsedMemory.length === 1) {
            gpuUsedSerie.append(0, gpuUsed[0])
            gpuUsedSerie.append(1 * root.deltaTime, gpuUsed[0])

            gpuUsedMemorySerie.append(0, gpuUsedMemory[0] * gpuMemoryRatio)
            gpuUsedMemorySerie.append(1 * root.deltaTime, gpuUsedMemory[0] * gpuMemoryRatio)

            gpuTemperatureSerie.append(0, gpuTemperature[0])
            gpuTemperatureSerie.append(1 * root.deltaTime, gpuTemperature[0])
            root.gpuMaxAxis = Math.max(gpuMaxAxis, gpuTemperature[0])
        } else {
            var displayLength = Math.min(maxDisplayLength, gpuUsedMemory.length)
            var step = gpuUsedMemory.length / displayLength
            for (var ii = 0; ii < displayLength; ii += step) {
                var i = Math.floor(ii*step)
                gpuUsedSerie.append(i * root.deltaTime, gpuUsed[i])

                gpuUsedMemorySerie.append(i * root.deltaTime, gpuUsedMemory[i] * gpuMemoryRatio)

                gpuTemperatureSerie.append(i * root.deltaTime, gpuTemperature[i])
                root.gpuMaxAxis = Math.max(gpuMaxAxis, gpuTemperature[i])
            }
        }
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
                            var _checked = checked;
                            for (var i = 0; i < cpuChart.count; ++i) {
                                cpuChart.series(i).visible = _checked
                            }
                        }
                    }

                    ChartViewLegend {
                        id: cpuLegend
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        chartView: cpuChart
                    }
                }
            }

            InteractiveChartView {
                id: cpuChart

                Layout.fillWidth: true
                Layout.preferredHeight: width / 2
                margins.top: 0
                margins.bottom: 0
                antialiasing: true

                legend.visible: false
                theme: ChartView.ChartThemeLight
                backgroundColor: "transparent"
                plotAreaColor: "transparent"
                titleColor: textColor

                visible: (root.fileVersion > 0.0)  // Only visible if we have valid information
                title: "CPU: " + root.nbCores + " cores, " + root.cpuFrequency + "MHz"

                ValueAxis {
                    id: valueCpuY
                    min: 0
                    max: 100
                    titleText: "<span style='color: " + textColor + "'>%</span>"
                    color: textColor
                    gridLineColor: textColor
                    minorGridLineColor: textColor
                    shadesColor: textColor
                    shadesBorderColor: textColor
                    labelsColor: textColor
                }

                ValueAxis {
                    id: valueCpuX
                    min: 0
                    max: root.deltaTime * Math.max(1, root.nbReads)
                    titleText: "<span style='color: " + textColor + "'>Minutes</span>"
                    color: textColor
                    gridLineColor: textColor
                    minorGridLineColor: textColor
                    shadesColor: textColor
                    shadesBorderColor: textColor
                    labelsColor: textColor
                }
            }

/**************************
***       RAM UI        ***
**************************/

            InteractiveChartView {
                id: ramChart
                margins.top: 0
                margins.bottom: 0
                Layout.fillWidth: true
                Layout.preferredHeight: width / 2
                antialiasing: true
                legend.color: textColor
                legend.labelColor: textColor
                legend.visible: false
                theme: ChartView.ChartThemeLight
                backgroundColor: "transparent"
                plotAreaColor: "transparent"
                titleColor: textColor

                visible: (root.fileVersion > 0.0)  // Only visible if we have valid information
                title: root.ramLabel + root.ramTotal + "GB"

                ValueAxis {
                    id: valueRamY
                    min: 0
                    max: 100
                    titleText: "<span style='color: " + textColor + "'>%</span>"
                    color: textColor
                    gridLineColor: textColor
                    minorGridLineColor: textColor
                    shadesColor: textColor
                    shadesBorderColor: textColor
                    labelsColor: textColor
                }

                ValueAxis {
                    id: valueRamX
                    min: 0
                    max: root.deltaTime * Math.max(1, root.nbReads)
                    titleText: "<span style='color: " + textColor + "'>Minutes</span>"
                    color: textColor
                    gridLineColor: textColor
                    minorGridLineColor: textColor
                    shadesColor: textColor
                    shadesBorderColor: textColor
                    labelsColor: textColor
                }
            }

/**************************
***       GPU UI        ***
**************************/

            InteractiveChartView {
                id: gpuChart

                Layout.fillWidth: true
                Layout.preferredHeight: width/2
                margins.top: 0
                margins.bottom: 0
                antialiasing: true
                legend.color: textColor
                legend.labelColor: textColor
                theme: ChartView.ChartThemeLight
                backgroundColor: "transparent"
                plotAreaColor: "transparent"
                titleColor: textColor

                visible: (root.fileVersion >= 2.0)  // No GPU information was collected before stats 2.0 fileVersion
                title: (root.gpuName || root.gpuTotalMemory) ? ("GPU: " + root.gpuName + ", " + root.gpuTotalMemory + "MB") : "No GPU"

                ValueAxis {
                    id: valueGpuY
                    min: 0
                    max: root.gpuMaxAxis
                    titleText: "<span style='color: " + textColor + "'>%, °C</span>"
                    color: textColor
                    gridLineColor: textColor
                    minorGridLineColor: textColor
                    shadesColor: textColor
                    shadesBorderColor: textColor
                    labelsColor: textColor
                }

                ValueAxis {
                    id: valueGpuX
                    min: 0
                    max: root.deltaTime * Math.max(1, root.nbReads)
                    titleText: "<span style='color: " + textColor + "'>Minutes</span>"
                    color: textColor
                    gridLineColor: textColor
                    minorGridLineColor: textColor
                    shadesColor: textColor
                    shadesBorderColor: textColor
                    labelsColor: textColor
                }
            }
        }
    }
}
