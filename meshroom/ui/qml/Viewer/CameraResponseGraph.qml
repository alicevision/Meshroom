import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Charts 1.0
import Controls 1.0
import DataObjects 1.0

FloatingPane {
    id: root

    property var responsePath: null
    property color textColor: Colors.sysPalette.text

    clip: true
    padding: 4

    CsvData {
        id: csvData
        filepath: responsePath
    }

    // To avoid interaction with components in background
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: {}
        onReleased: {}
        onWheel: {}
    }

    // Note: We need to use csvData.getNbColumns() slot instead of the csvData.nbColumns property to avoid a crash on linux.
    property bool crfReady: csvData && csvData.ready && (csvData.getNbColumns() >= 4)
    onCrfReadyChanged: {
        responseChart.removeAllSeries()
        if (crfReady) {
            var xCol = csvData.getColumn(0).content
            var curveColors = ["red", "green", "blue"]
            for (var ci = 1; ci <= 3; ci++) {
                var col = csvData.getColumn(ci)
                var points = []
                for (var i = 0; i < col.content.length; i++) {
                    points.push({ x: parseFloat(xCol[i]), y: parseFloat(col.content[i]) })
                }
                responseChart.addSeries(col.title, curveColors[ci - 1], points)
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 10

            ChartViewCheckBox {
                text: "ALL"
                color: root.textColor
                checkState: crfLegend.buttonGroup.checkState
                leftPadding: 0
                onClicked: responseChart.setAllSeriesVisible(checked)
            }

            LineChartLegend {
                id: crfLegend
                Layout.fillWidth: true
                chartView: responseChart
            }
        }

        LineChart {
            id: responseChart

            Layout.fillWidth: true
            Layout.preferredHeight: width * 0.75

            textColor: root.textColor
            title: "Camera Response Function (CRF)"
            xAxisTitle: "Camera Brightness"
            yAxisTitle: "Normalized Radiance"
            xMin: crfReady ? parseFloat(csvData.getColumn(0).getFirst()) : 0
            xMax: crfReady ? parseFloat(csvData.getColumn(0).getLast()) : 1
            yMin: 0.0
            yMax: 1.0
        }
    }
}
