import QtQuick 2.5

Connections {

    target: null

    // project actions
    onSelectProject: {
        currentProject = _applicationModel.projects.get(id).modelData;
        selectJob(0);
        _stack.push({ item: _stack.mainPage, replace:(_stack.depth>1) });
    }
    onCloseCurrentProject: {
        _stack.pop();
        currentProject = null;
        currentJob = null;
    }
    onOpenProjectDialog: {
        var dialog = _appDialogs.openProject.createObject(_appWindow);
        dialog.open();
    }
    onOpenProjectDirectory: {
        Qt.openUrlExternally(currentProject.url);
    }
    onOpenProjectSettings: {
        var dialog = _appDialogs.projectSettingsDialog.createObject(_appWindow);
        dialog.open();
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
        currentJob = currentProject.jobs.get(id).modelData;
    }
    onAddJob: {
        currentProject.jobs.addJob(currentProject.url);
        selectJob(currentProject.jobs.count-1);
    }
    onDuplicateJob: {
        currentProject.jobs.duplicateJob(currentJob);
        selectJob(currentProject.jobs.count-1);
    }
    onDeleteJob: {
        if(currentJob.isStoredOnDisk()) {
            var dialog = _appDialogs.jobDeletionDialog.createObject(_appWindow);
            dialog.open();
            return;
        }
        currentProject.jobs.removeJob(currentJob);
    }
    onOpenJobSubmissionDialog: {
        var dialog = _appDialogs.jobSubmissionDialog.createObject(_appWindow);
        dialog.open();
    }
    onSubmitJob: {
        currentJob.start(locally);
    }
    onOpenJobDirectory: {
        Qt.openUrlExternally(currentJob.url);
    }
    onOpenJobSettings: {
        var dialog = _appDialogs.jobSettingsDialog.createObject(_appWindow);
        dialog.open();
    }
    onRefreshJobStatus: {
        currentJob.refresh();
    }

    // other actions
    onOpenImageSelectionDialog: {
        var dialog = _appDialogs.imageSelectionDialog.createObject(_appWindow);
        dialog.onImageSelected.connect(callback);
        dialog.open();
    }
}
