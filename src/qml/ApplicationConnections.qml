import QtQuick 2.5

Connections {

    target: null

    // project actions
    onSelectProject: {
        currentProject = _application.projects.get(id).modelData;
        selectJob(0);
        _applicationStack.push({ item: _applicationStack.mainPage, replace:(_applicationStack.depth>1) });
    }
    onCloseCurrentProject: {
        _applicationStack.pop();
        currentProject = defaultProject;
        currentJob = defaultJob;
    }
    onOpenProjectDialog: {
        var dialog = _applicationDialogs.openProject.createObject(_applicationWindow);
        dialog.open();
    }
    onOpenProjectDirectory: {
        Qt.openUrlExternally(currentProject.url);
    }
    onOpenProjectSettings: {
        var dialog = _applicationDialogs.projectSettingsDialog.createObject(_applicationWindow);
        dialog.open();
    }
    onAddProject: {
        _application.projects.addProject(url);
        selectProject(_application.projects.count-1);
    }
    onRemoveProject: {
        _application.projects.removeProject(_application.projects.get(id).modelData);
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
    onRemoveJob: {
        if(currentJob.isStoredOnDisk()) {
            var dialog = _applicationDialogs.jobDeletionDialog.createObject(_applicationWindow);
            dialog.open();
            return;
        }
        currentJob.erase();
        var jobToDelete = currentJob;
        currentJob = defaultJob;
        currentProject.jobs.removeJob(jobToDelete);
        selectJob(currentProject.jobs.count-1);
    }
    onOpenJobSubmissionDialog: {
        var dialog = _applicationDialogs.jobSubmissionDialog.createObject(_applicationWindow);
        dialog.open();
    }
    onSubmitJob: {
        currentJob.start(locally);
    }
    onOpenJobDirectory: {
        Qt.openUrlExternally(currentJob.url);
    }
    onOpenJobSettings: {
        var dialog = _applicationDialogs.jobSettingsDialog.createObject(_applicationWindow);
        dialog.open();
    }
    onRefreshJobStatus: {
        currentJob.refresh();
    }

    // other actions
    onOpenImageSelectionDialog: {
        var dialog = _applicationDialogs.imageSelectionDialog.createObject(_applicationWindow);
        dialog.onImageSelected.connect(callback);
        dialog.open();
    }
    onOpenFullscreenImageDialog: {
        var dialog = _applicationDialogs.fullscreenImageDialog.createObject(_applicationWindow);
        dialog.url = url;
        dialog.open();
    }
}
