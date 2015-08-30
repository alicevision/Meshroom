import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "../layouts"
import "../delegates"
import "../headers"
import "../components"
import "../forms"

TitledPageLayout {

    background: Rectangle {
        color: _style.window.color.darker
    }
    header: MenuHeader {}
    body: ScrollView {
        width: parent.width
        ListView {
            model: _applicationModel.projects
            delegate: ProjectDelegate {
                onProjectSelected: showProjectPage(projectID)
                onJobSelected: showJobPage(projectID, jobID)
            }
            spacing: 0
            interactive: false
        }
    }

}
