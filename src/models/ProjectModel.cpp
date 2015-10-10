#include "ProjectModel.hpp"
#include "io/SettingsIO.hpp"
#include <QQmlEngine>
#include <QDebug>

namespace mockup
{

ProjectModel::ProjectModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

int ProjectModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _projects.count();
}

QVariant ProjectModel::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _projects.count())
        return QVariant();
    Project* project = _projects[index.row()];
    switch(role)
    {
        case NameRole:
            return project->name();
        case UrlRole:
            return project->url();
        case JobsRole:
            return QVariant::fromValue(project->jobs());
        case ProxyRole:
            return QVariant::fromValue(project->proxy());
        case ModelDataRole:
            return QVariant::fromValue(project);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> ProjectModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
    roles[UrlRole] = "url";
    roles[JobsRole] = "jobs";
    roles[ProxyRole] = "proxy";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void ProjectModel::addProject(Project* project)
{
    beginInsertRows(QModelIndex(), rowCount(), rowCount());

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(project, QQmlEngine::CppOwnership);
    project->setParent(this);

    _projects << project;
    endInsertRows();
    emit countChanged(rowCount());

    SettingsIO::saveRecentProjects(this);
}

void ProjectModel::addProject(const QUrl& url)
{
    Project* project = new Project(url);
    addProject(project);
}

void ProjectModel::removeProject(Project* project)
{
    int id = _projects.indexOf(project);
    if(id < 0)
        return;
    beginRemoveRows(QModelIndex(), id, id);
    _projects.removeAt(id);
    delete project;
    endRemoveRows();
    emit countChanged(rowCount());

    SettingsIO::saveRecentProjects(this);
}

} // namespace
