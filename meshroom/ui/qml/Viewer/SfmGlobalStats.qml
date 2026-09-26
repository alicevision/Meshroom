import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import AliceVision 1.0 as AliceVision
import Charts 1.0
import Controls 1.0
import Utils 1.0

FloatingPane {
    id: root

    property var msfmData
    property var mTracks
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

    // Colors assigned to the 6 statistical curves (Min, Max, Mean, Median, Q1, Q3)
    readonly property var statColors: ["#4169e1", "#dc143c", "#228b22", "#ff8c00", "#9932cc", "#20b2aa"]

    GridLayout {
        anchors.fill: parent
        columns: 2

        // Residuals Per View chart
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
                    checkState: residualsPerViewLegend.buttonGroup.checkState
                    onClicked: residualsPerViewChart.setAllSeriesVisible(checked)
                }
                LineChartLegend {
                    id: residualsPerViewLegend
                    Layout.fillWidth: true
                    chartView: residualsPerViewChart
                }
            }
            LineChart {
                id: residualsPerViewChart
                Layout.fillWidth: true
                Layout.fillHeight: true
                textColor: root.textColor
                title: "Residuals Per View"
                xAxisTitle: "Ordered Views"
                yAxisTitle: "Reprojection Error (pix)"
                xMin: 0
                xMax: sfmDataStat.residualsPerViewMaxAxisX
                yMin: 0
                yMax: sfmDataStat.residualsPerViewMaxAxisY
            }
        }

        // Landmarks Per View chart
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
                    checkState: landmarksFeatTracksPerViewLegend.buttonGroup.checkState
                    onClicked: landmarksPerViewChart.setAllSeriesVisible(checked)
                }
                LineChartLegend {
                    id: landmarksFeatTracksPerViewLegend
                    Layout.fillWidth: true
                    chartView: landmarksPerViewChart
                }
            }
            LineChart {
                id: landmarksPerViewChart
                Layout.fillWidth: true
                Layout.fillHeight: true
                textColor: root.textColor
                title: "Landmarks Per View"
                xAxisTitle: "Ordered Views"
                yAxisTitle: "Number of Landmarks"
                xMin: 0
                xMax: sfmDataStat.landmarksPerViewMaxAxisX
                yMin: 0
                yMax: sfmDataStat.landmarksPerViewMaxAxisY
            }
        }

        // Observations Lengths Per View chart
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
                    checkState: observationsLengthsPerViewLegend.buttonGroup.checkState
                    onClicked: observationsLengthsPerViewChart.setAllSeriesVisible(checked)
                }
                LineChartLegend {
                    id: observationsLengthsPerViewLegend
                    Layout.fillWidth: true
                    chartView: observationsLengthsPerViewChart
                }
            }
            LineChart {
                id: observationsLengthsPerViewChart
                Layout.fillWidth: true
                Layout.fillHeight: true
                textColor: root.textColor
                title: "Observations Lengths Per View"
                xAxisTitle: "Ordered Views"
                yAxisTitle: "Observations Lengths"
                xMin: 0
                xMax: sfmDataStat.observationsLengthsPerViewMaxAxisX
                yMin: 0
                yMax: sfmDataStat.observationsLengthsPerViewMaxAxisY
            }
        }

        // (empty fourth cell)
        Item { Layout.fillWidth: true; Layout.fillHeight: true }
    }

    // Stats from the sfmData
    AliceVision.MSfMDataStats {
        id: sfmDataStat
        msfmData: root.msfmData
        mTracks: root.mTracks

        onAxisChanged: {
            landmarksPerViewChart.removeAllSeries()
            landmarksPerViewChart.addSeries("Landmarks", root.statColors[0], sfmDataStat.getLandmarksPerViewPoints())
            landmarksPerViewChart.addSeries("Tracks", root.statColors[1], sfmDataStat.getTracksPerViewPoints())

            residualsPerViewChart.removeAllSeries()
            residualsPerViewChart.addSeries("Min",    root.statColors[0], sfmDataStat.getResidualsMinPerViewPoints())
            residualsPerViewChart.addSeries("Max",    root.statColors[1], sfmDataStat.getResidualsMaxPerViewPoints())
            residualsPerViewChart.addSeries("Mean",   root.statColors[2], sfmDataStat.getResidualsMeanPerViewPoints())
            residualsPerViewChart.addSeries("Median", root.statColors[3], sfmDataStat.getResidualsMedianPerViewPoints())
            residualsPerViewChart.addSeries("Q1",     root.statColors[4], sfmDataStat.getResidualsFirstQuartilePerViewPoints())
            residualsPerViewChart.addSeries("Q3",     root.statColors[5], sfmDataStat.getResidualsThirdQuartilePerViewPoints())

            observationsLengthsPerViewChart.removeAllSeries()
            observationsLengthsPerViewChart.addSeries("Min",    root.statColors[0], sfmDataStat.getObservationsLengthsMinPerViewPoints())
            observationsLengthsPerViewChart.addSeries("Max",    root.statColors[1], sfmDataStat.getObservationsLengthsMaxPerViewPoints())
            observationsLengthsPerViewChart.addSeries("Mean",   root.statColors[2], sfmDataStat.getObservationsLengthsMeanPerViewPoints())
            observationsLengthsPerViewChart.addSeries("Median", root.statColors[3], sfmDataStat.getObservationsLengthsMedianPerViewPoints())
            observationsLengthsPerViewChart.addSeries("Q1",     root.statColors[4], sfmDataStat.getObservationsLengthsFirstQuartilePerViewPoints())
            observationsLengthsPerViewChart.addSeries("Q3",     root.statColors[5], sfmDataStat.getObservationsLengthsThirdQuartilePerViewPoints())
        }
    }
}

