import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.3

import "layouts"
import "delegates"
import "headers"
import "components"

SplittedPageLayout {

    id: root

    header: Item {}
    bodyA: MenuPage {}
    bodyB: JobPage {
        projectModel: _applicationModel.currentProject
        jobModel: _applicationModel.currentProject.currentJob
    }
    footer: LogBar {
        model: _applicationModel.logs
    }
}
