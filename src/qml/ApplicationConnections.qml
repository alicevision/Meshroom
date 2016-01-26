import QtQuick 2.5

Connections {

    target: null

    // project actions
    onSelectProject: {
        currentProject = _applicationModel.projects.get(id);
        selectJob(0);
        _stack.push({ item: _stack.mainPage, replace:(_stack.depth>1) });
    }
    onCloseCurrentProject: {
        _stack.pop();
        currentProject = null;
    }
    onOpenProjectDialog: {
        _appDialogs.openProject.open();
    }
    onOpenProjectDirectory: {
        Qt.openUrlExternally(currentProject.url);
    }
    onOpenProjectSettings: {
        _appDialogs.projectSettingsDialog.open();
    }
    onAddProject: {
        _applicationModel.projects.addProject(url);
        selectProject(_applicationModel.projects.count-1);
    }
    onRemoveProject: {
        _applicationModel.projects.removeProject(_applicationModel.projects.get(id).modelData);
    }

    // job actions
    onSelectJob: {
        currentJob = currentProject.jobs.get(id);
    }
    onAddJob: {
        currentProject.jobs.addJob(currentProject.url);
        selectJob(currentProject.jobs.count-1);
    }
    onDeleteJob: {
        _appDialogs.jobDeletionDialog.open();
    }
    onOpenJobSubmissionDialog: {
        _appDialogs.jobSubmissionDialog.open();
    }
    onSubmitJob: {
        currentJob.modelData.start(locally);
    }
    onOpenJobDirectory: {
        Qt.openUrlExternally(currentJob.url);
    }
    onOpenJobSettings: {
        _appDialogs.jobSettingsDialog.open();
    }
    onRefreshJobStatus: {
        currentJob.modelData.refresh();
    }

}
