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

    visible: (_currentScene.sfm && _currentScene.sfm.isComputed) ? root.visible : false
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

    GridLayout {
        anchors.fill: parent
        columns: 2

        // Reprojection Errors chart
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 10
                ChartViewCheckBox {
                    text: "ALL"
                    color: textColor
                    leftPadding: 0
                    checkState: residualLegend.buttonGroup.checkState
                    onClicked: residualChart.setAllSeriesVisible(checked)
                }
                LineChartLegend {
                    id: residualLegend
                    Layout.fillWidth: true
                    chartView: residualChart
                }
            }
            LineChart {
                id: residualChart
                Layout.fillWidth: true
                Layout.fillHeight: true
                textColor: root.textColor
                title: "Reprojection Errors"
                xAxisTitle: "Reprojection Error"
                yAxisTitle: "Number of Points"
                xMin: 0
                xMax: viewStat.residualMaxAxisX
                yMin: 0
                yMax: viewStat.residualMaxAxisY
            }
        }

        // Observations Scale chart
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 10
                ChartViewCheckBox {
                    text: "ALL"
                    color: textColor
                    leftPadding: 0
                    checkState: observationsScaleLegend.buttonGroup.checkState
                    onClicked: observationsScaleChart.setAllSeriesVisible(checked)
                }
                LineChartLegend {
                    id: observationsScaleLegend
                    Layout.fillWidth: true
                    chartView: observationsScaleChart
                }
            }
            LineChart {
                id: observationsScaleChart
                Layout.fillWidth: true
                Layout.fillHeight: true
                textColor: root.textColor
                title: "Observations Scale"
                xAxisTitle: "Scale"
                yAxisTitle: "Number of Points"
                xMin: 0
                xMax: viewStat.observationsScaleMaxAxisX
                yMin: 0
                yMax: viewStat.observationsScaleMaxAxisY
            }
        }

        // Observations Lengths chart
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: 10
                ChartViewCheckBox {
                    text: "ALL"
                    color: textColor
                    leftPadding: 0
                    checkState: observationsLengthsLegend.buttonGroup.checkState
                    onClicked: observationsLengthsChart.setAllSeriesVisible(checked)
                }
                LineChartLegend {
                    id: observationsLengthsLegend
                    Layout.fillWidth: true
                    chartView: observationsLengthsChart
                }
            }
            LineChart {
                id: observationsLengthsChart
                Layout.fillWidth: true
                Layout.fillHeight: true
                textColor: root.textColor
                title: "Observations Lengths"
                xAxisTitle: "Observations Length"
                yAxisTitle: "Number of Points"
                xMin: 2
                xMax: viewStat.observationsLengthsMaxAxisX
                yMin: 0
                yMax: viewStat.observationsLengthsMaxAxisY
            }
        }

        // (empty fourth cell)
        Item { Layout.fillWidth: true; Layout.fillHeight: true }
    }

    // Stats from a view the sfmData
    AliceVision.MViewStats {
        id: viewStat
        msfmData: (root.visible && root.msfmData && root.msfmData.status === AliceVision.MSfMData.Ready) ? root.msfmData : null
        viewId: root.viewId
        onViewStatsChanged: {
            residualChart.removeAllSeries()
            residualChart.addSeries("Average on All Cameras", "#dc143c", viewStat.getResidualFullPoints())
            residualChart.addSeries("Current", "#00008b", viewStat.getResidualViewPoints())

            observationsLengthsChart.removeAllSeries()
            observationsLengthsChart.addSeries("All Cameras", "#dc143c", viewStat.getObservationsLengthsFullPoints())
            observationsLengthsChart.addSeries("Current", "#00008b", viewStat.getObservationsLengthsViewPoints())

            observationsScaleChart.removeAllSeries()
            observationsScaleChart.addSeries("Average on All Cameras", "#dc143c", viewStat.getObservationsScaleFullPoints())
            observationsScaleChart.addSeries("Current", "#00008b", viewStat.getObservationsScaleViewPoints())
        }
    }
}

