import QtQuick 2.5
import QtQuick.Layouts 1.2
import DarkStyle.Controls 1.0
import DarkStyle 1.0
import Meshroom.Job 0.1
import Meshroom.Project 0.1
import Logger 1.0
import QtQuick.Window 2.2
import "pages"


ApplicationWindow {

    id: _applicationWindow

    // parameters
    width: Screen.width/2
    height: Screen.height/2
    visible: true
    color: "#111"
    title: Qt.application.name

    // properties
    property variant defaultProject: Project {}
    property variant defaultJob: Job {}
    property variant currentProject: defaultProject
    property variant currentJob: defaultJob

    // actions
    signal selectProject(int id)
    signal addProject(string url)
    signal removeProject(int id)
    signal closeProject()
    signal openProjectDirectory()
    signal openProjectSettings()
    signal openProjectDialog()
    signal selectJob(int id)
    signal addJob()
    signal duplicateJob()
    signal removeJob()
    signal submitJob(bool locally)
    signal refreshJob()
    signal importJobImages(var files)
    signal openJobDirectory()
    signal openJobSettings()
    signal openJobSubmissionDialog()
    signal openImageSelectionDialog(var callback)
    signal openImportImageDialog()
    signal showCameras(bool checked)
    signal showGrid(bool checked)
    signal jobPageTabChanged(int index)

    // connections
    ApplicationConnections {}

    // menus & dialogs
    ApplicationMenu {}
    ApplicationDialogs { id: _applicationDialogs }

    // main content
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        StackView {
            id: _applicationStack
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
