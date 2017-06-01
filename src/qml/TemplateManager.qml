import QtQuick 2.7
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.0
import Meshroom.Scene 1.0
import Meshroom.TemplateCollection 1.0

ColumnLayout {
    id: root

    property alias scene: templateManager.scene
    property alias graph: templateManager.graph

    states: [
        State {
            when: !scene
            name: "INACTIVE"
            PropertyChanges {
                target: templateCB
                currentIndex: -1
            }
            PropertyChanges {
                target: templateManager
                active: false
            }
        }
    ]

    ComboBox {
        id: templateCB
        property variant template: null
        Layout.preferredWidth: 300
        Layout.alignment: Qt.AlignHCenter
        model: _application.templates
        textRole: "name"
        currentIndex: -1
        displayText: currentIndex < 0 ? "Select a Template" : currentText
        onCurrentIndexChanged: {
            template = model.data(model.index(currentIndex, 0), TemplateCollection.ModelDataRole);
            console.log("Loading " + template.url)
            _application.openTemplate(template)
        }
    }

    Loader {
        id: templateManager
        Layout.fillHeight: true
        Layout.fillWidth: true
        Layout.margins: 4

        property variant scene
        property variant graph: scene ? scene.graph : null
        source: active ? templateCB.template.url.toString().replace(".meshroom", ".qml") : ""
    }

}
