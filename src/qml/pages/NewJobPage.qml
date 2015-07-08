import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1

import "layouts"
import "../components/forms"
import "../components/delegates"
import "../components/gallery"
import "../components/headers"
import Popart 0.1

TitledPageLayout {

    id : root

    // project model
    property variant model: null

    // page #0
    property Component page0: ResourceDropArea {
        function removeResource() {
            if(root.body != page0)
                return;
            root.model.tmpJob.removeResources(gallery.getSelectionList());
        }
        onFilesDropped: root.model.tmpJob.addResources(files);
        ResourceGallery {
            id: gallery
            anchors.fill: parent
            anchors.margins: 30
            model: root.model.tmpJob
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
        model: root.model.tmpJob
    }

    Component.onCompleted: {
        root.model.newTmpJob();
    }

    // header
    header: BreadcrumbHeader {
        model: ListModel {
            ListElement { name: "image selection" }
            ListElement { name: "job settings" }
        }
        onCrumbChanged: {
            if(index == model.count) {
                // job added properly
                if(root.model.addTmpJob()) {
                    stackView.pop();
                    return;
                }
                // an error occurred
                popupDialog.popup(root.model.tmpJob.errorString());
                return;
            }
            // change page
            body = eval("page"+index);
        }
        onActionCancelled: {
            // root.model.clearTmpJob();
            stackView.pop();
        }
    }
    body: page0
}
