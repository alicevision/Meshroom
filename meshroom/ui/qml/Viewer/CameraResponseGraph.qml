import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import QtCharts

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
        if (crfReady) {
            redCurve.clear()
            greenCurve.clear()
            blueCurve.clear()
            csvData.getColumn(1).fillChartSerie(redCurve)
            csvData.getColumn(2).fillChartSerie(greenCurve)
            csvData.getColumn(3).fillChartSerie(blueCurve)
        } else {
            redCurve.clear()
            greenCurve.clear()
            blueCurve.clear()
        }
    }
    Item {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenterOffset: -responseChart.width/2
        anchors.verticalCenterOffset: -responseChart.height/2

        InteractiveChartView {
            id: responseChart
            width: root.width > 400 ? 400 : (root.width < 350 ? 350 : root.width)
            height: width * 0.75

            title: "Camera Response Function (CRF)"
            legend.visible: false
            antialiasing: true

            ValueAxis {
                id: valueAxisX
                labelFormat: "%i"
                titleText: "Camera Brightness"
                min: crfReady ? csvData.getColumn(0).getFirst() : 0
                max: crfReady ? csvData.getColumn(0).getLast() : 1
            }
            ValueAxis {
                id: valueAxisY
                titleText: "Normalized Radiance"
                min: 0.0
                max: 1.0
            }

            // We cannot use a Repeater with these Components so we need to instantiate them one by one
            LineSeries {
                // Red curve
                id: redCurve
                axisX: valueAxisX
                axisY: valueAxisY
                name: crfReady ? csvData.getColumn(1).title : ""
                color: name.toLowerCase()
            }
            LineSeries {
                // Green curve
                id: greenCurve
                axisX: valueAxisX
                axisY: valueAxisY
                name: crfReady ? csvData.getColumn(2).title : ""
                color: name.toLowerCase()
            }
            LineSeries {
                // Blue curve
                id: blueCurve
                axisX: valueAxisX
                axisY: valueAxisY
                name: crfReady ? csvData.getColumn(3).title : ""
                color: name.toLowerCase()
            }
        }

        Item {
            id: btnContainer

            anchors.bottom: responseChart.bottom
            anchors.bottomMargin: 35
            anchors.left: responseChart.left
            anchors.leftMargin: responseChart.width * 0.15

            RowLayout {
                ChartViewCheckBox {
                    text: "ALL"
                    color: textColor
                    checkState: legend.buttonGroup.checkState
                    onClicked: {
                        const _checked = checked
                        for (let i = 0; i < responseChart.count; ++i) {
                            responseChart.series(i).visible = _checked
                        }
                    }
                }

                ChartViewLegend {
                    id: legend
                    chartView: responseChart
                }
            }
        }
    }
}
