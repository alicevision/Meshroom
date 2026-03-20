import QtQuick
import QtQuick.Controls

/**
 * LineChartLegend is an interactive legend component for LineChart.
 *
 * It provides a labeled, colored CheckBox for each series in the associated
 * LineChart, allowing the user to toggle series visibility.
 *
 *  • Click            – toggle the clicked series on/off
 *  • Ctrl + Click     – show only the clicked series (solo mode)
 *  • Hover            – highlight the hovered series, dim the others
 *
 * The component exposes a ButtonGroup so that an "ALL" master checkbox can
 * display the aggregate check state of all legend items.
 */

Flow {
    id: root

    /// The LineChart instance whose series this legend represents
    property var chartView: null

    /// Expose the internal ButtonGroup so callers can read its checkState
    readonly property ButtonGroup buttonGroup: legendGroup

    ButtonGroup {
        id: legendGroup
        exclusive: false
    }

    // ---- Internal model rebuilt from chartView whenever series change -------

    ListModel { id: seriesModel }

    function _rebuild() {
        seriesModel.clear()
        if (!chartView) return
        for (var i = 0; i < chartView.count; i++) {
            var s = chartView.series(i)
            if (!s) continue
            seriesModel.append({
                seriesIndex: i,
                seriesName:  s.name,
                seriesColor: s.color.toString(),
                seriesVisible: s.visible
            })
        }
    }

    onChartViewChanged: {
        seriesModel.clear()
        if (chartView) {
            chartView.seriesAdded.connect(_rebuild)
            chartView.seriesRemoved.connect(_rebuild)
            chartView.seriesChanged.connect(_rebuild)
            _rebuild()
        }
    }

    // ---- Legend items -------------------------------------------------------

    Repeater {
        model: seriesModel

        ChartViewCheckBox {
            id: legendItem

            ButtonGroup.group: legendGroup

            checked: model.seriesVisible
            text:    model.seriesName
            color:   model.seriesColor

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true

                onEntered: {
                    if (!chartView) return
                    for (var i = 0; i < chartView.count; i++) {
                        if (chartView.series(i) && chartView.series(i).visible) {
                            chartView.setSeriesLineWidth(
                                i, i === model.seriesIndex ? 3.0 : 0.5)
                        }
                    }
                }

                onExited: {
                    if (!chartView) return
                    for (var i = 0; i < chartView.count; i++) {
                        chartView.setSeriesLineWidth(i, 1.5)
                    }
                }

                onClicked: function(mouse) {
                    if (!chartView) return
                    if (mouse.modifiers & Qt.ControlModifier) {
                        // Solo: hide everything except the clicked series
                        chartView.setAllSeriesVisible(false)
                        chartView.setSeriesVisible(model.seriesIndex, true)
                    } else {
                        var cur = chartView.series(model.seriesIndex)
                        if (cur) chartView.setSeriesVisible(model.seriesIndex, !cur.visible)
                    }
                }
            }
        }
    }
}
