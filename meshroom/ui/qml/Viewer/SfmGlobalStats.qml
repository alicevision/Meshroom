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

    property var msfmData
    property var mTracks
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
        id: residualsPerViewChart
        width: parent.width * 0.5
        height: parent.height * 0.5

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
            titleText: "Reprojection Error (pix)"
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
        LineSeries {
            id: residualsFirstQuartilePerViewLineSerie
            axisX: residualsPerViewValueAxisX
            axisY: residualsPerViewValueAxisY
            name: "Q1"
        }
        LineSeries {
            id: residualsThirdQuartilePerViewLineSerie
            axisX: residualsPerViewValueAxisX
            axisY: residualsPerViewValueAxisY
            name: "Q3"
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
                    for (var i = 0; i < residualsPerViewChart.count; ++i) {
                        residualsPerViewChart.series(i).visible = _checked
                    }
                }
            }

            ChartViewLegend {
                id: residualsPerViewLegend
                chartView: residualsPerViewChart
            }

        }
    }

    InteractiveChartView {
        id: observationsLengthsPerViewChart
        width: parent.width * 0.5
        height: parent.height * 0.5
        anchors.top: parent.top
        anchors.topMargin: (parent.height) * 0.5

        title: "Observations Lengths Per View"
        legend.visible: false
        antialiasing: true

        ValueAxis {
            id: observationsLengthsPerViewValueAxisX
            labelFormat: "%i"
            titleText: "Ordered Views"
            min: 0
            max: sfmDataStat.observationsLengthsPerViewMaxAxisX
        }
        ValueAxis {
            id: observationsLengthsPerViewValueAxisY
            titleText: "Observations Lengths"
            min: 0
            max: sfmDataStat.observationsLengthsPerViewMaxAxisY
            tickAnchor: 0
            tickInterval: 0.50
            tickCount: sfmDataStat.observationsLengthsPerViewMaxAxisY * 2
        }

        LineSeries {
            id: observationsLengthsMinPerViewLineSerie
            axisX: observationsLengthsPerViewValueAxisX
            axisY: observationsLengthsPerViewValueAxisY
            name: "Min"
        }
        LineSeries {
            id: observationsLengthsMaxPerViewLineSerie
            axisX: observationsLengthsPerViewValueAxisX
            axisY: observationsLengthsPerViewValueAxisY
            name: "Max"
        }
        LineSeries {
            id: observationsLengthsMeanPerViewLineSerie
            axisX: observationsLengthsPerViewValueAxisX
            axisY: observationsLengthsPerViewValueAxisY
            name: "Mean"
        }
        LineSeries {
            id: observationsLengthsMedianPerViewLineSerie
            axisX: observationsLengthsPerViewValueAxisX
            axisY: observationsLengthsPerViewValueAxisY
            name: "Median"
        }
        LineSeries {
            id: observationsLengthsFirstQuartilePerViewLineSerie
            axisX: observationsLengthsPerViewValueAxisX
            axisY: observationsLengthsPerViewValueAxisY
            name: "Q1"
        }
        LineSeries {
            id: observationsLengthsThirdQuartilePerViewLineSerie
            axisX: observationsLengthsPerViewValueAxisX
            axisY: observationsLengthsPerViewValueAxisY
            name: "Q3"
        }
    }

    Item {
        id: observationsLengthsPerViewBtnContainer

        Layout.fillWidth: true
        anchors.bottom: observationsLengthsPerViewChart.bottom
        anchors.bottomMargin: 35
        anchors.left: observationsLengthsPerViewChart.left
        anchors.leftMargin: observationsLengthsPerViewChart.width * 0.25

        RowLayout {
            ChartViewCheckBox {
                id: allModes
                text: "ALL"
                color: textColor
                checkState: observationsLengthsPerViewLegend.buttonGroup.checkState
                onClicked: {
                    var _checked = checked;
                    for (var i = 0; i < observationsLengthsPerViewChart.count; ++i) {
                        observationsLengthsPerViewChart.series(i).visible = _checked
                    }
                }
            }

            ChartViewLegend {
                id: observationsLengthsPerViewLegend
                chartView: observationsLengthsPerViewChart
            }
        }
    }

    InteractiveChartView {
        id: landmarksPerViewChart
        width: parent.width * 0.5
        height: parent.height * 0.5
        anchors.left: parent.left
        anchors.leftMargin: (parent.width) * 0.5
        anchors.top: parent.top

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
            name: "Landmarks"
        }
        LineSeries {
            id: tracksPerViewLineSerie
            axisX: landmarksPerViewValueAxisX
            axisY: landmarksPerViewValueAxisY
            name: "Tracks"
        }
    }

    Item {
        id: landmarksFeatTracksPerViewBtnContainer

        Layout.fillWidth: true
        anchors.bottom: landmarksPerViewChart.bottom
        anchors.bottomMargin: 35
        anchors.left: landmarksPerViewChart.left
        anchors.leftMargin: landmarksPerViewChart.width * 0.25

        RowLayout {
            ChartViewCheckBox {
                id: allFeatures
                text: "ALL"
                color: textColor
                checkState: landmarksFeatTracksPerViewLegend.buttonGroup.checkState
                onClicked: {
                    var _checked = checked;
                    for (var i = 0; i < landmarksPerViewChart.count; ++i) {
                        landmarksPerViewChart.series(i).visible = _checked
                    }
                }
            }

            ChartViewLegend {
                id: landmarksFeatTracksPerViewLegend
                chartView: landmarksPerViewChart
            }
        }
    }

    // Stats from the sfmData
    AliceVision.MSfMDataStats {
        id: sfmDataStat
        msfmData: root.msfmData
        mTracks: root.mTracks

        onAxisChanged: {
            fillLandmarksPerViewSerie(landmarksPerViewLineSerie)
            fillTracksPerViewSerie(tracksPerViewLineSerie)
            fillResidualsMinPerViewSerie(residualsMinPerViewLineSerie)
            fillResidualsMaxPerViewSerie(residualsMaxPerViewLineSerie)
            fillResidualsMeanPerViewSerie(residualsMeanPerViewLineSerie)
            fillResidualsMedianPerViewSerie(residualsMedianPerViewLineSerie)
            fillResidualsFirstQuartilePerViewSerie(residualsFirstQuartilePerViewLineSerie)
            fillResidualsThirdQuartilePerViewSerie(residualsThirdQuartilePerViewLineSerie)
            fillObservationsLengthsMinPerViewSerie(observationsLengthsMinPerViewLineSerie)
            fillObservationsLengthsMaxPerViewSerie(observationsLengthsMaxPerViewLineSerie)
            fillObservationsLengthsMeanPerViewSerie(observationsLengthsMeanPerViewLineSerie)
            fillObservationsLengthsMedianPerViewSerie(observationsLengthsMedianPerViewLineSerie)
            fillObservationsLengthsFirstQuartilePerViewSerie(observationsLengthsFirstQuartilePerViewLineSerie)
            fillObservationsLengthsThirdQuartilePerViewSerie(observationsLengthsThirdQuartilePerViewLineSerie)
        }
    }
}
