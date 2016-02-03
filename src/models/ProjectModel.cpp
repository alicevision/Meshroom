#include "ProjectModel.hpp"
#include "io/SettingsIO.hpp"
#include <QQmlEngine>
#include <QDebug>

namespace meshroom
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

bool ProjectModel::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if(index.row() < 0 || index.row() >= _projects.count())
        return false;
    Project* project = _projects[index.row()];
    switch(role)
    {
        case NameRole:
            project->setName(value.toString());
            break;
        default:
            return false;
    }
    emit dataChanged(index, index);
    return true;
}

void ProjectModel::addProject(Project* project)
{
    beginInsertRows(QModelIndex(), rowCount(), rowCount());

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(project, QQmlEngine::CppOwnership);
    project->setParent(this);
    connect(project, SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)),
            this, SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)));

    _projects << project;
    endInsertRows();

    QModelIndex id = index(rowCount() - 1, 0);
    project->setModelIndex(id);

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

QVariantMap ProjectModel::get(int row) const
{
    QHash<int, QByteArray> names = roleNames();
    QHashIterator<int, QByteArray> i(names);
    QVariantMap result;
    while(i.hasNext())
    {
        i.next();
        QModelIndex idx = index(row, 0);
        QVariant data = idx.data(i.key());
        result[i.value()] = data;
    }
    return result;
}

} // namespace
