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

import AliceVision 1.0 as AliceVision


FloatingPane {
    id: root

    property var msfmData
    property color textColor: Colors.sysPalette.text

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
        id: landmarksPerViewChart
        width: parent.width * 0.5
        height: parent.height * 0.5

        title: "Landmarks Per View"
        legend.visible: false
        antialiasing: true

        ValueAxis {
            id: landmarksPerViewValueAxisX
            titleText: "Ordered Views"
            min: 0.0
            max: sfmDataStat.landmarksPerViewMaxAxisX
        }
        ValueAxis {
            id: landmarksPerViewValueAxisY
            labelFormat: "%i"
            titleText: "Number of Landmarks"
            min: 0
            max: sfmDataStat.landmarksPerViewMaxAxisY
        }
        LineSeries {
            id: landmarksPerViewLineSerie
            axisX: landmarksPerViewValueAxisX
            axisY: landmarksPerViewValueAxisY
        }
    }

    InteractiveChartView {
        id: residualsPerViewChart
        width: parent.width * 0.5
        height: parent.height * 0.5
        anchors.top: parent.top
        anchors.topMargin: (parent.height) * 0.5

        title: "Residuals Per View"
        legend.visible: false
        antialiasing: true

        ValueAxis {
            id: residualsPerViewValueAxisX
            labelFormat: "%i"
            titleText: "Ordered Views"
            min: 0
            max: sfmDataStat.residualsPerViewMaxAxisX
        }
        ValueAxis {
            id: residualsPerViewValueAxisY
            titleText: "Percentage of residuals"
            min: 0
            max: sfmDataStat.residualsPerViewMaxAxisY
            tickAnchor: 0
            tickInterval: 0.50
            tickCount: sfmDataStat.residualsPerViewMaxAxisY * 2
        }
        LineSeries {
            id: residualsMinPerViewLineSerie
            axisX: residualsPerViewValueAxisX
            axisY: residualsPerViewValueAxisY
            name: "Min"
        }
        LineSeries {
            id: residualsMaxPerViewLineSerie
            axisX: residualsPerViewValueAxisX
            axisY: residualsPerViewValueAxisY
            name: "Max"
        }
        LineSeries {
            id: residualsMeanPerViewLineSerie
            axisX: residualsPerViewValueAxisX
            axisY: residualsPerViewValueAxisY
            name: "Mean"
        }
        LineSeries {
            id: residualsMedianPerViewLineSerie
            axisX: residualsPerViewValueAxisX
            axisY: residualsPerViewValueAxisY
            name: "Median"
        }
    }

    Item {
        id: residualsPerViewBtnContainer

        Layout.fillWidth: true
        anchors.bottom: residualsPerViewChart.bottom
        anchors.bottomMargin: 35
        anchors.left: residualsPerViewChart.left
        anchors.leftMargin: residualsPerViewChart.width * 0.25

        RowLayout {

            ChartViewCheckBox {
                id: allObservations
                text: "ALL"
                color: textColor
                checkState: residualsPerViewLegend.buttonGroup.checkState
                onClicked: {
                    var _checked = checked;
                    for(var i = 0; i < residualsPerViewChart.count; ++i)
                    {
                        residualsPerViewChart.series(i).visible = _checked;
                    }
                }
            }

            ChartViewLegend {
                id: residualsPerViewLegend
                chartView: residualsPerViewChart
            }

        }
    }

    // Stats from the sfmData
    AliceVision.MSfMDataStats {
        id: sfmDataStat
        msfmData: (root.visible && root.msfmData && root.msfmData.status === AliceVision.MSfMData.Ready) ? root.msfmData : null
        onStatsChanged: {
            console.warn("QML AliceVision.MSfMDataStats statsChanged: " + sfmDataStat.msfmData);
            fillLandmarksPerViewSerie(landmarksPerViewLineSerie);
            fillResidualsMinPerViewSerie(residualsMinPerViewLineSerie);
            fillResidualsMaxPerViewSerie(residualsMaxPerViewLineSerie);
            fillResidualsMeanPerViewSerie(residualsMeanPerViewLineSerie);
            fillResidualsMedianPerViewSerie(residualsMedianPerViewLineSerie);
        }
    }
}
