import QtQuick 2.2
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.3

import "layouts"
import "delegates"
import "headers"
import "components"

SplittedPageLayout {

    id: root

    header: Item {}
    bodyA: MenuPage {}
    bodyB: Loader {
        sourceComponent: _private.currentComponent
    }
    footer: LogBar {
        model: _applicationModel.logs
    }

    // private properties
    QtObject {
        id: _private
        property int currentProjectID: 0
        property int currentJobID: 0
        property Component currentComponent: homePage
    }

    // available pages (bodyB)
    property Component homePage: HomePage {
    }
    property Component projectPage: ProjectPage {
        projectModel: _applicationModel.projects[_private.currentProjectID]
    }
    property Component jobPage: JobPage {
        projectModel: _applicationModel.projects[_private.currentProjectID]
        jobModel: _applicationModel.projects[_private.currentProjectID].jobs[_private.currentJobID]
    }

    // functions
    function showHomePage() {
        _private.currentProjectID = -1;
        _private.currentJobID = -1;
        _private.currentComponent = homePage;
    }
    function showProjectPage(projectID) {
        _private.currentProjectID = projectID;
        _private.currentJobID = -1;
        _private.currentComponent = projectPage;
    }
    function showJobPage(projectID, jobID) {
        _private.currentProjectID = projectID;
        _private.currentJobID = jobID;
        _private.currentComponent = jobPage;
    }
    function isCurrentProject(projectID) {
        return (_private.currentProjectID == projectID);
    }
    function isCurrentJob(projectID, jobID) {
        return (isCurrentProject(projectID) && _private.currentJobID == jobID);
    }
    function currentProjectID() {
        return _private.currentProjectID;
    }
    function currentJobID() {
        return _private.currentJobID;
    }
    function removeProject() {
        _applicationModel.removeProject(_applicationModel.projects[_private.currentProjectID]);
    }
    function addJob() {
        _applicationModel.projects[_private.currentProjectID].addJob();
    }

}
