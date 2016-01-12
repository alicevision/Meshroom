import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import QtQml.Models 2.2
import Logger 1.0
import "pages"

ApplicationWindow {

    id: _appWindow

    property variant currentProject: null
    property variant currentJob: null

    // project actions
    signal selectProject(int id)
    signal closeCurrentProject()
    signal openProjectDialog()
    signal openProjectDirectory()
    signal openProjectSettings()
    signal addProject(string url)
    signal removeProject(int id)
    // job actions
    signal selectJob(int id)
    signal addJob()
    signal startJob(bool locally)
    signal openJobDirectory()
    signal refreshJobStatus()

    ApplicationSettings { target: _appWindow }
    ApplicationConnections { target: _appWindow }
    ApplicationMenu {}
    ApplicationDialogs { id: _appDialogs }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        StackView {
            id: _stack
            Layout.fillWidth: true
            Layout.fillHeight: true
            property Component homePage: HomePage {}
            property Component mainPage: MainPage {}
            initialItem: homePage
            focus: true
        }
        LogBar {
            property bool expanded: false
            Layout.fillWidth: true
            Layout.preferredHeight: expanded ? parent.height/3 : 30
            Behavior on Layout.preferredHeight { NumberAnimation {}}
            color: Style.window.color.xdark
            onToggle: expanded = !expanded
        }
    }

}
