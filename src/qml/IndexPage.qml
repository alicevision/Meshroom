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
    function addProject(projectURL) {
        var newProject = _applicationModel.addNewProject();
        newProject.url = projectURL;
        newProject.save();
        if(newProject.jobs.length==0)
            addJob(_applicationModel.projects.length-1);
        else
            showProjectPage(_applicationModel.projects.length-1);
    }
    function removeProject(projectID) {
        _applicationModel.removeProject(_applicationModel.projects[projectID]);
        var projectCount = _applicationModel.projects.length;
        if(projectID>=projectCount)
            (projectCount==0) ? showHomePage() : showProjectPage(projectID-1);
        else
            showProjectPage(projectID);
    }
    function addJob(projectID) {
        _applicationModel.projects[projectID].addJob();
        showJobPage(projectID, _applicationModel.projects[projectID].jobs.length-1);
    }
    function removeJob(projectID, jobID) {
        _applicationModel.projects[projectID].removeJob(_applicationModel.projects[projectID].jobs[jobID]);
        var jobCount = _applicationModel.projects[projectID].jobs.length;
        if(jobID>=jobCount)
            (jobCount==0) ? showProjectPage(projectID) : showJobPage(projectID, jobCount-1);
        else
            showJobPage(projectID, jobID);
    }

}
