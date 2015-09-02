import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "layouts"
import "delegates"
import "headers"
import "components"

TitledPageLayout {

    id: root

    background: DefaultBackground {}
    header: MenuHeader {}
    body: CustomScrollView {
        width: parent.width
        ListView {
            model: _applicationModel.projects
            delegate: ProjectDelegate {
                onProjectSelected: showProjectPage(projectID)
                onProjectRemoved: removeProject(projectID)
                onJobSelected: showJobPage(projectID, jobID)
                onJobAdded: addJob(projectID)
            }
            spacing: 0
            interactive: false
        }
    }

}
