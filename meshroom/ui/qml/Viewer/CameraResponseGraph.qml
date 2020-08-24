import QtQuick 2.9
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import MaterialIcons 2.2
import QtPositioning 5.8
import QtLocation 5.9
import QtCharts 2.13
import Charts 1.0

import Controls 1.0
import Utils 1.0
import DataObjects 1.0

FloatingPane {
    id: root

    property var ldrHdrCalibrationNode: null
    property color textColor: Colors.sysPalette.text

    clip: true
    padding: 4

    CsvData {
        id: csvData
        property bool hasAttr: (ldrHdrCalibrationNode && ldrHdrCalibrationNode.hasAttribute("response"))
        filepath: hasAttr ? ldrHdrCalibrationNode.attribute("response").value : ""
    }

    // To avoid interaction with components in background
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: {}
        onReleased: {}
        onWheel: {}
    }

    // note: We need to use csvData.getNbColumns() slot instead of the csvData.nbColumns property to avoid a crash on linux.
    property bool crfReady: csvData && csvData.ready && (csvData.getNbColumns() >= 4)
    onCrfReadyChanged: {
        if(crfReady)
        {
            redCurve.clear()
            greenCurve.clear()
            blueCurve.clear()
            csvData.getColumn(1).fillChartSerie(redCurve)
            csvData.getColumn(2).fillChartSerie(greenCurve)
            csvData.getColumn(3).fillChartSerie(blueCurve)
        }
        else
        {
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
            // Red curve
            LineSeries {
                id: redCurve
                axisX: valueAxisX
                axisY: valueAxisY
                name: crfReady ? csvData.getColumn(1).title : ""
                color: name.toLowerCase()
            }
            // Green curve
            LineSeries {
                id: greenCurve
                axisX: valueAxisX
                axisY: valueAxisY
                name: crfReady ? csvData.getColumn(2).title : ""
                color: name.toLowerCase()
            }
            // Blue curve
            LineSeries {
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
                        for(let i = 0; i < responseChart.count; ++i) {
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
