import QtQuick
import QtQuick.Controls
import QtCharts

/**
 * ChartViewLegend is an interactive legend component for ChartViews.
 * It provides a CheckBox for each series that can control its visibility,
 * and highlight on hovering.
 */

Flow {
    id: root

    // The ChartView to create the legend for
    property ChartView chartView
    // Currently hovered series
    property var hoveredSeries: null

   readonly property ButtonGroup buttonGroup: ButtonGroup {
        id: legendGroup
        exclusive: false
    }

    /// Shortcut function to clear legend
    function clear() {
        seriesModel.clear()
    }

    // Update internal ListModel when ChartView's series change
    Connections {
        target: chartView
        function onSeriesAdded(series) {
            seriesModel.append({"series": series})
        }
        function onSeriesRemoved(series) {
            for (var i = 0; i < seriesModel.count; ++i) {
                if (seriesModel.get(i)["series"] === series) {
                    seriesModel.remove(i)
                    return
                }
            }
        }
    }

    onChartViewChanged: {
        clear()
        for (var i = 0; i < chartView.count; ++i)
            seriesModel.append({"series": chartView.series(i)})
    }

    Repeater {
        // ChartView series can't be accessed directly as a model.
        // Use an intermediate ListModel populated with those series.
        model: ListModel {
            id: seriesModel
        }

        ChartViewCheckBox {
            ButtonGroup.group: legendGroup

            checked: series.visible
            text: series.name
            color: series.color

            onHoveredChanged: {
                if (hovered && series.visible)
                    root.hoveredSeries = series
                else
                    root.hoveredSeries = null
            }

            // Hovered serie properties override
            states: [
                State {
                    when: series && root.hoveredSeries === series
                    PropertyChanges { target: series; width: 5.0 }
                },
                State {
                    when: series && root.hoveredSeries && root.hoveredSeries !== series
                    PropertyChanges { target: series; width: 0.2 }
                }
            ]

            MouseArea {
                anchors.fill: parent
                onClicked: function(mouse) {
                    if (mouse.modifiers & Qt.ControlModifier)
                        root.soloSeries(index)
                    else
                        series.visible = !series.visible
                }
            }
        }
    }

    /// Hide all series but the one at index 'idx'
    function soloSeries(idx) {
        for (var i = 0; i < seriesModel.count; i++) {
            chartView.series(i).visible = false
        }
        chartView.series(idx).visible = true
    }
}
