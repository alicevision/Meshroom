import QtQuick 2.5

Item {

    Connections {
        target: Qt.application
        onAboutToQuit: {
            currentJob = defaultJob;
            currentProject = defaultProject;
        }
    }

    Connections {
        target: _applicationWindow
        onSelectProject: {
            currentProject = _application.projects.get(id).modelData;
            selectJob(0);
            _applicationStack.push({ item: _applicationStack.mainPage, replace:(_applicationStack.depth>1) });
        }
        onAddProject: {
            _application.projects.addProject(url);
            selectProject(_application.projects.count-1);
        }
        onRemoveProject: {
            _application.projects.removeProject(_application.projects.get(id).modelData);
        }
        onCloseProject: {
            _applicationStack.pop();
            currentProject = defaultProject;
            currentJob = defaultJob;
        }
        onOpenProjectDirectory: {
            Qt.openUrlExternally(currentProject.url);
        }
        onOpenProjectSettings: {
            var dialog = _applicationDialogs.projectSettingsDialog.createObject(_applicationWindow);
            dialog.open();
        }
        onOpenProjectDialog: {
            var dialog = _applicationDialogs.openProject.createObject(_applicationWindow);
            dialog.open();
        }
        onSelectJob: {
            currentJob = currentProject.jobs.get(id).modelData;
        }
        onAddJob: {
            currentProject.jobs.addJob();
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
        onSubmitJob: {
            currentJob.start(locally);
        }
        onRefreshJob: {
            currentJob.refresh();
        }
        onImportJobImages: {
            for(var i=0; i<files.length; ++i)
            currentJob.images.addResource(files[i]);
        }
        onOpenJobDirectory: {
            Qt.openUrlExternally(currentJob.url);
        }
        onOpenJobSettings: {
            var dialog = _applicationDialogs.jobSettingsDialog.createObject(_applicationWindow);
            dialog.open();
        }
        onOpenJobSubmissionDialog: {
            var dialog = _applicationDialogs.jobSubmissionDialog.createObject(_applicationWindow);
            dialog.open();
        }
        onOpenImageSelectionDialog: {
            var dialog = _applicationDialogs.imageSelectionDialog.createObject(_applicationWindow);
            dialog.onImageSelected.connect(callback);
            dialog.open();
        }
        onOpenImportImageDialog: {
            var dialog = _applicationDialogs.importImageDialog.createObject(_applicationWindow);
            dialog.open();
        }
    }
}
