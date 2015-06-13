import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.3

import "layouts"
import "../components/delegates"
import "../components/headers"

TitledPageLayout {

    header: OverviewHeader {}
    body: ListView {
        model: _applicationModel.projects
        delegate: JobListDelegate {}
        spacing: 0
        clip: true
    }

}
