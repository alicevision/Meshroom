#include "SettingsIO.hpp"
#include "models/ApplicationModel.hpp"
#include "models/ProjectModel.hpp"
#include <QSettings>
#include <QUrl>
#include <iostream>

namespace mockup
{

void SettingsIO::clearAll()
{
    QSettings settings;
    settings.clear();
}

void SettingsIO::clearRecentProjects()
{
    QSettings settings;
    QVariantList empty;
    settings.setValue("project/recent", empty);
}

void SettingsIO::loadRecentProjects(ApplicationModel& applicationModel)
{
    QSettings settings;
    QVariantList recents = settings.value("project/recent").toList();
    QVariantList::iterator it = recents.begin();
    QList<QObject*> projects;
    while(it != recents.end())
    {
        QUrl url(it->toUrl());
        applicationModel.addProject(url);
        ++it;
    }
}

void SettingsIO::saveRecentProjects(ApplicationModel& applicationModel)
{
    // clear recent project list
    SettingsIO::clearRecentProjects();
    // rebuild it by iterating over all loaded projects
    QSettings settings;
    QVariantList recents;
    const QList<QObject*>& projects = applicationModel.projects();
    QObjectList::const_iterator it = projects.begin();
    while(it != projects.end())
    {
        ProjectModel* project = dynamic_cast<ProjectModel*>(*it);
        if(project)
            recents.push_front(project->url());
        ++it;
    }
    settings.setValue("project/recent", recents);
}

} // namespace
