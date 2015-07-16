import QtQuick 2.2
import QtQuick.Controls 1.3

import "../layouts"
import "../forms"
import "../headers"

TitledPageLayout {

    id: root
    property variant model: null // project model

    // page #0
    property Component page0: ProjectSettingsForm {
        model: root.model
    }

    // header
    header: BreadcrumbHeader {
        model: ListModel {
            ListElement { name: "project settings" }
        }
        onCrumbChanged: {
            if(index == model.count) {
                if(root.model.save())
                    stackView.pop();
                return;
            }
            body = eval("page"+index);
        }
        onActionCancelled: {
            _applicationModel.removeProject(root.model);
            stackView.pop();
        }
    }
    body: page0
}
