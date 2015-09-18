import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2

import "layouts"
import "delegates"
import "headers"
import "components"

SplittedPageLayout {

    id: root
    property variant currentProject: null
    property variant currentJob: null

    header: Item {}
    bodyA: MenuPage {}
    bodyB: JobPage {}
    footer: LogBar {
        model: _applicationModel.logs
    }
}
