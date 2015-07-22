import QtQuick 2.2
import QtQuick.Controls 1.3

import "../components"

Item {
    anchors.fill: parent
    StackView {
        id: stackView
        anchors.fill: parent
        focus: true
        initialItem: OverviewPage {}
    }
    LogBar {
        model: _applicationModel.logs
    }
}
