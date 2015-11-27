import QtQuick 2.5

Connections {

    target: null

    onSelectProject: {
        currentProject = _projects.items.get(id).model
        currentJob = _jobs.items.get(0).model
    }

    onOpenProject: {
        _applicationModel.projects.addProject(url);
        selectProject(_applicationModel.projects.count-1);
    }

    onOpenProjectLocation: {
        _appDialogs.openProject.open();
    }

    onOpenProjectDirectory: {
    }

    onCloseProject: {
    }

    // onOpenJobDirectory: {
    // }
    //
    // onAddJob: {
    // }
    //
    // onRemoveEmptyJobs: {
    // }
    //
    // onStartJob: {
    // }
    //
    // onRefreshJob: {
    // }
    //
    // onShowHome: {
    // }
    //
    // onShowProjectSettings: {
    // }
    //
    // onShowJobSettings: {
    // }
    //
    // onToggleJobSettings: {
    // }
}
