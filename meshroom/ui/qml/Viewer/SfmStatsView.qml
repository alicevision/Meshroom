import QtCharts
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import AliceVision 1.0 as AliceVision
import Charts 1.0
import Controls 1.0
import Utils 1.0


FloatingPane {
    id: root

    property var msfmData: null
    property int viewId
    property color textColor: Colors.sysPalette.text

    visible: (_reconstruction.sfm && _reconstruction.sfm.isComputed) ? root.visible : false
    clip: true
    padding: 4

    // To avoid interaction with components in background
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onPressed: {}
        onReleased: {}
        onWheel: {}
    }

    InteractiveChartView {
        id: residualChart
        width: parent.width * 0.5
        height: parent.height * 0.5

        title: "Reprojection Errors"
        legend.visible: false
        antialiasing: true

        ValueAxis {
            id: residualValueAxisX
            titleText: "Reprojection Error"
            min: 0.0
            max: viewStat.residualMaxAxisX
        }
        ValueAxis {
            id: residualValueAxisY
            labelFormat: "%i"
            titleText: "Number of Points"
            min: 0
            max: viewStat.residualMaxAxisY
        }
        LineSeries {
            id: residualFullLineSerie
            axisX: residualValueAxisX
            axisY: residualValueAxisY
            name: "Average on All Cameras"
        }
        LineSeries {
            id: residualViewLineSerie
            axisX: residualValueAxisX
            axisY: residualValueAxisY
            name: "Current"
        }
    }

    Item {
        id: residualBtnContainer

        Layout.fillWidth: true
        anchors.bottom: residualChart.bottom
        anchors.bottomMargin: 35
        anchors.left: residualChart.left
        anchors.leftMargin: residualChart.width * 0.15

        RowLayout {

            ChartViewCheckBox {
                id: allResiduals
                text: "ALL"
                color: textColor
                checkState: residualLegend.buttonGroup.checkState
                onClicked: {
                    var _checked = checked;
                    for (var i = 0; i < residualChart.count; ++i) {
                        residualChart.series(i).visible = _checked
                    }
                }
            }

            ChartViewLegend {
                id: residualLegend
                chartView: residualChart
            }
        }
    }

    InteractiveChartView {
        id: observationsLengthsChart
        width: parent.width * 0.5
        height: parent.height * 0.5
        anchors.top: parent.top
        anchors.topMargin: (parent.height) * 0.5

        legend.visible: false
        title: "Observations Lengths"

        ValueAxis {
            id: observationsLengthsvalueAxisX
            labelFormat: "%i"
            titleText: "Observations Length"
            min: 2
            max: viewStat.observationsLengthsMaxAxisX
            tickAnchor: 2
            tickInterval: 1
            tickCount: 5
        }
        ValueAxis {
            id: observationsLengthsvalueAxisY
            labelFormat: "%i"
            titleText: "Number of Points"
            min: 0
            max: viewStat.observationsLengthsMaxAxisY
        }
        LineSeries {
            id: observationsLengthsFullLineSerie
            axisX: observationsLengthsvalueAxisX
            axisY: observationsLengthsvalueAxisY
            name: "All Cameras"
        }
        LineSeries {
            id: observationsLengthsViewLineSerie
            axisX: observationsLengthsvalueAxisX
            axisY: observationsLengthsvalueAxisY
            name: "Current"
        }
    }

    Item {
        id: observationsLengthsBtnContainer

        Layout.fillWidth: true
        anchors.bottom: observationsLengthsChart.bottom
        anchors.bottomMargin: 35
        anchors.left: observationsLengthsChart.left
        anchors.leftMargin: observationsLengthsChart.width * 0.25

        RowLayout {
            ChartViewCheckBox {
                id: allObservations
                text: "ALL"
                color: textColor
                checkState: observationsLengthsLegend.buttonGroup.checkState
                onClicked: {
                    var _checked = checked;
                    for (var i = 0; i < observationsLengthsChart.count; ++i) {
                        observationsLengthsChart.series(i).visible = _checked
                    }
                }
            }

            ChartViewLegend {
                id: observationsLengthsLegend
                chartView: observationsLengthsChart
            }
        }
    }

    InteractiveChartView {
        id: observationsScaleChart
        width: parent.width * 0.5
        height: parent.height * 0.5
        anchors.left: parent.left
        anchors.leftMargin: (parent.width) * 0.5
        anchors.top: parent.top

        legend.visible: false
        title: "Observations Scale"

        ValueAxis {
            id: observationsScaleValueAxisX
            titleText: "Scale"
            min: 0
            max: viewStat.observationsScaleMaxAxisX
        }
        ValueAxis {
            id: observationsScaleValueAxisY
            titleText: "Number of Points"
            min: 0
            max: viewStat.observationsScaleMaxAxisY
        }
        LineSeries {
            id: observationsScaleFullLineSerie
            axisX: observationsScaleValueAxisX
            axisY: observationsScaleValueAxisY
            name: " Average on All Cameras"
        }
        LineSeries {
            id: observationsScaleViewLineSerie
            axisX: observationsScaleValueAxisX
            axisY: observationsScaleValueAxisY
            name: "Current"
        }
    }

    Item {
        id: observationsScaleBtnContainer

        Layout.fillWidth: true
        anchors.bottom: observationsScaleChart.bottom
        anchors.bottomMargin: 35
        anchors.left: observationsScaleChart.left
        anchors.leftMargin: observationsScaleChart.width * 0.15

        RowLayout {
            ChartViewCheckBox {
                id: allObservationsScales
                text: "ALL"
                color: textColor
                checkState: observationsScaleLegend.buttonGroup.checkState
                onClicked: {
                    var _checked = checked;
                    for (var i = 0; i < observationsScaleChart.count; ++i) {
                        observationsScaleChart.series(i).visible = _checked
                    }
                }
            }

            ChartViewLegend {
                id: observationsScaleLegend
                chartView: observationsScaleChart
            }
        }
    }

    // Stats from a view the sfmData
    AliceVision.MViewStats {
        id: viewStat
        msfmData: (root.visible && root.msfmData && root.msfmData.status === AliceVision.MSfMData.Ready) ? root.msfmData : null
        viewId: root.viewId
        onViewStatsChanged: {
            fillResidualFullSerie(residualFullLineSerie)
            fillResidualViewSerie(residualViewLineSerie)
            fillObservationsLengthsFullSerie(observationsLengthsFullLineSerie)
            fillObservationsLengthsViewSerie(observationsLengthsViewLineSerie)
            fillObservationsScaleFullSerie(observationsScaleFullLineSerie)
            fillObservationsScaleViewSerie(observationsScaleViewLineSerie)
        }
    }
}
