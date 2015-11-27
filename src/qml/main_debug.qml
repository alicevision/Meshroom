import QtQuick 2.5
import DarkStyle.Controls 1.0
import QtQml.Models 2.2
import Logger 1.0

ApplicationWindow {

    id: _appWindow
    property variant currentProject: null
    property variant currentJob: null

    signal selectProject(int id)
    signal openProject(int id)
    signal openProjectLocation()
    signal openProjectDirectory()
    signal addProject(string url)
    signal closeProject()
    signal openJobDirectory()
    signal addJob()
    signal removeEmptyJobs()
    signal startJob()
    signal refreshJob()
    signal showHome()
    signal showProjectSettings()
    signal showJobSettings()
    signal toggleJobSettings()

    ApplicationSettings { target: _appWindow }
    ApplicationConnections { target: _appWindow }
    ApplicationMenu {}
    ApplicationDialogs { id: _appDialogs }

    DelegateModel {
        id: _jobs
        model: currentProject.proxy
        delegate: Rectangle { width: parent.width }
        Component.onCompleted: currentJob = items.get(0).model
    }
    DelegateModel {
        id: _projects
        model: _applicationModel.projects
        delegate: Rectangle { width: parent.width }
        Component.onCompleted: currentProject = items.get(0).model
    }
    onCurrentProjectChanged: {
        currentProject? stack.push({ item: stack.mainPage }) : stack.pop();
    }

    StackView {
        id: stack
        property Component homePage: Rectangle { color: "red" }
        property Component mainPage: Rectangle { color: "green" }
        anchors.fill: parent
        initialItem: homePage
    }

    LogBar {
    }

}
