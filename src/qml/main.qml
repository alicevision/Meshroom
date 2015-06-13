import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Dialogs 1.1
// import Popart 0.1

import "pages"
import "styles"
import "components/forms"

ApplicationWindow {

    id: root
    width: 800
    height: 800
    visible: true
    style: DefaultStyle.application

    // GLVideoStreamView {
    //     anchors.fill: parent
    //     color: "black"
    // }

    PopupDialog {
        id: popupDialog
    }

    StackView {
        id: stackView
        anchors.fill: parent
        focus: true
        Keys.onReleased: {
            if(event.key === Qt.Key_Escape) {
                root.style = DefaultStyle.applicationDebug;
            }
        }
        initialItem: OverviewPage {}
    }
}
