import QtQuick 2.2
import QtQuick.Controls 1.3

import "layouts"
import "../components/forms"
import "../components/gallery"
import "../components/headers"

TitledPageLayout {

    id: root

    // page #0
    property Component page0: ProjectSettingsForm {
        model: _applicationModel.tmpProject()
    }

    // header
    header: BreadcrumbHeader {
        model: ListModel {
            ListElement { name: "project settings" }
        }
        onCrumbChanged: {
            if(index == model.count) {
                // project added properly
                if(_applicationModel.addTmpProject()) {
                    stackView.pop();
                    return;
                }
                // an error occurred
                popupDialog.popup(_applicationModel.tmpProject().errorString());
                return;
            }
            // change page
            body = eval("page"+index);
        }
    }
    body: page0
}
