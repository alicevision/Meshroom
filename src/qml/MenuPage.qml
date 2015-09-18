import QtQuick 2.5
import QtQuick.Layouts 1.2
import QtQuick.Controls 1.4

import "layouts"
import "delegates"
import "headers"
import "components"

TitledPageLayout {

    id: root

    background: DefaultBackground {}
    header: Item {}
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
