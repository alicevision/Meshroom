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
        property Component currentComponent: homePage
    }

    // available pages (bodyB)
    property Component homePage: HomePage {
    }
    property Component projectPage: ProjectPage {
        projectModel: _applicationModel.currentProject
    }
    property Component jobPage: JobPage {
        projectModel: _applicationModel.currentProject
        jobModel: _applicationModel.currentProject.currentJob
    }

    // functions
    function selectHomePage() {
        _private.currentComponent = homePage;
    }
    function selectProjectPage(projectModel) {
        _applicationModel.currentProject = projectModel;
        _private.currentComponent = (projectModel)?projectPage:homePage;
    }
    function selectJobPage(projectModel, jobModel) {
        _applicationModel.currentProject = projectModel;
        projectModel.currentJob = jobModel;
        _private.currentComponent = (jobModel)?jobPage:projectPage;
    }
    function addProject(projectURL) {
        var newProject = _applicationModel.addNewProject();
        newProject.url = projectURL;
        newProject.save();
        selectJobPage(newProject, newProject.currentJob);
    }
    function removeProject(projectModel) {
        _applicationModel.removeProject(projectModel);
        selectProjectPage(_applicationModel.currentProject);
    }
    function addJob(projectModel) {
        var newJob = projectModel.addJob();
        selectJobPage(projectModel, newJob);
    }
    function removeJob(projectModel, jobModel) {
        projectModel.removeJob(jobModel);
        selectJobPage(projectModel, projectModel.currentJob);
    }

}
