#include "SettingsIO.hpp"
#include "Application.hpp"
#include "models/ProjectModel.hpp"
#include <QSettings>
#include <QUrl>

namespace mockup
{

SettingsIO::SettingsIO(Application& app)
    : QObject(&app)
    , _application(app)
{
}

void SettingsIO::load() const
{
    QVariantList recents = recentProjects();
    QVariantList::iterator it = recents.begin();
    QList<QObject*> projects;
    while(it != recents.end())
    {
        QUrl url((*it).toUrl());
        // in case of readable project
        if(url.isValid())
        {
            ProjectModel* project = new ProjectModel(url, &_application);
            if(project->error() == ProjectModel::ERR_NOERROR)
            {
                projects.append(project);
                ++it;
                continue;
            }
        }
        // in case of invalid project
        removeFromRecentProjects(url);
        ++it;
    }
    _application.model().setProjects(projects);
}

void SettingsIO::clear() const
{
    QSettings settings;
    settings.clear();
}

void SettingsIO::clearRecentProjects() const
{
    QSettings settings;
    QVariantList empty;
    settings.setValue("project/recent", empty);
}

QVariantList SettingsIO::recentProjects() const
{
    QSettings settings;
    return settings.value("project/recent").toList();
}

void SettingsIO::addToRecentProjects(const QUrl& url) const
{
    QSettings settings;
    QVariantList recents = settings.value("project/recent").toList();
    recents.removeAll(url);
    recents.push_front(url);
    settings.setValue("project/recent", recents);
}

void SettingsIO::removeFromRecentProjects(const QUrl& url) const
{
    QSettings settings;
    QVariantList recents = settings.value("project/recent").toList();
    recents.removeAll(url);
    settings.setValue("project/recent", recents);
}

} // namespace
