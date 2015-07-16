import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

import "../layouts"
import "../components"
import "../forms"
import "../delegates"
import "../headers"
import Popart 0.1

TitledPageLayout {

    id : root
    property variant model: null // job model
    property variant projectModel: null // project model

    // page #0
    property Component page0: ResourceDropArea {
        function removeResource() {
            if(root.body != page0)
                return;
            root.model.removeResources(gallery.getSelectionList());
        }
        onFilesDropped: root.model.addResources(files);
        ResourceGallery {
            id: gallery
            anchors.fill: parent
            anchors.margins: 30
            model: root.model
            selectable: true
            Shortcut {
                key: "Backspace"
                onActivated: removeResource()
            }
            Shortcut {
                key: "Delete"
                onActivated: removeResource()
            }
        }
    }

    // page #1
    property Component page1: JobSettingsForm {
        model: root.model
    }

    // header
    header: BreadcrumbHeader {
        model: ListModel {
            ListElement { name: "image selection" }
            ListElement { name: "job settings" }
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
            root.projectModel.removeJob(root.model);
            stackView.pop();
        }
    }
    body: page0
}
