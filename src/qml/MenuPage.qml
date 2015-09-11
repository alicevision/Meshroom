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
            delegate: ProjectDelegate {}
            spacing: 0
            interactive: false
        }
    }

}
