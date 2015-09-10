import QtQuick 2.2
import QtQuick.Controls 1.3

import "styles"

ApplicationWindow {

    id: _mainWindow

    width: 800
    height: 800
    visible: true
    style: _style.bggl
    title: "mockup"

    // main application style sheet
    DefaultStyle {
        id: _style
    }

    // // main loader, needed to enable instant coding
    // Loader {
    //     id: _mainLoader
    //     anchors.fill: parent
    //     objectName: "instanCodingLoader"
    //     source: (_applicationModel.projects.length>0)?"IndexPage.qml":"HomePage.qml"
    // }

    StackView {
        id: stack
        anchors.fill: parent
        property Component indexPage: IndexPage {}
        initialItem: HomePage {}
        Component.onCompleted: {
            if(_applicationModel.projects.length>0)
                stack.push({item:stack.indexPage, immediate: true});
        }
        Connections {
            target: _applicationModel
            onProjectsChanged: {
                if(_applicationModel.projects.length>0 && stack.depth==1)
                    stack.push({item:stack.indexPage});
                else if(_applicationModel.projects.length==0 && stack.depth>1)
                    stack.pop();
            }
        }
        delegate: StackViewDelegate {
            function transitionFinished(properties) {
                properties.exitItem.opacity = 1;
                _mainWindow.style = _style.bggl;
            }
            pushTransition: StackViewTransition {
                ScriptAction { script: _mainWindow.style = _style.bg; }
                PropertyAnimation {
                    target: enterItem
                    property: "opacity"
                    from: 0
                    to: 1
                }
                PropertyAnimation {
                    target: exitItem
                    property: "opacity"
                    from: 1
                    to: 0
                }
            }
        }
    }
}
