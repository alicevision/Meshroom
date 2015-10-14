#include "SettingsIO.hpp"
#include "models/ProjectModel.hpp"
#include "models/ResourceModel.hpp"
#include <QSettings>
#include <QUrl>
#include <QDir>
#include <cstdlib> // std::getenv

namespace meshroom
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

void SettingsIO::loadRecentProjects(ProjectModel* projectModel)
{
    QSettings settings;
    QVariantList recents = settings.value("project/recent").toList();
    QVariantList::iterator it = recents.begin();
    QList<QObject*> projects;
    while(it != recents.end())
    {
        QUrl url(it->toUrl());
        projectModel->addProject(url);
        ++it;
    }
}

void SettingsIO::saveRecentProjects(ProjectModel* projectModel)
{
    // clear recent project list
    SettingsIO::clearRecentProjects();
    // rebuild it by iterating over all loaded projects
    QSettings settings;
    QVariantList recents;
    for(size_t i = 0; i < projectModel->rowCount(); ++i)
    {
        QModelIndex id = projectModel->index(i, 0);
        Project* p = projectModel->data(id, ProjectModel::ModelDataRole).value<Project*>();
        if(!p || !p->url().isValid())
            continue;
        recents.append(p->url());
    }
    settings.setValue("project/recent", recents);
}

void SettingsIO::loadFeaturedProjects(ResourceModel* featuredModel)
{
    QString externalLocationsStr = std::getenv("MESHROOM_PROJECT_LOCATIONS");
    QStringList externalLocations = externalLocationsStr.split(":");
    foreach(const QString& loc, externalLocations)
    {
        QDir dir(loc);
        if(QUrl::fromLocalFile(loc).isValid() && dir.exists())
        {
            Resource* r = new Resource(QUrl::fromLocalFile(loc));
            featuredModel->addResource(r);
        }
    }
}

} // namespace
