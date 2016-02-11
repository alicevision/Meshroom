#include "JobModel.hpp"
#include "Project.hpp"
#include <QQmlEngine>
#include <cassert>

namespace meshroom
{

JobModel::JobModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

int JobModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _jobs.count();
}

QVariant JobModel::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _jobs.count())
        return QVariant();
    Job* job = _jobs[index.row()];
    switch(role)
    {
        case UrlRole:
            return job->url();
        case NameRole:
            return job->name();
        case DateRole:
            return job->date();
        case UserRole:
            return job->user();
        case CompletionRole:
            return job->completion();
        case StatusRole:
            return job->status();
        case ThumbnailRole:
            return job->thumbnail();
        case StepsRole:
            return QVariant::fromValue(job->steps());
        case ImagesRole:
            return QVariant::fromValue(job->images());
        case ModelDataRole:
            return QVariant::fromValue(job);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> JobModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[UrlRole] = "url";
    roles[NameRole] = "name";
    roles[DateRole] = "date";
    roles[UserRole] = "user";
    roles[CompletionRole] = "completion";
    roles[StatusRole] = "status";
    roles[ThumbnailRole] = "thumbnail";
    roles[StepsRole] = "steps";
    roles[ImagesRole] = "images";
    roles[ModelDataRole] = "modelData";
    return roles;
}

bool JobModel::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if(index.row() < 0 || index.row() >= _jobs.count())
        return false;
    Job* job = _jobs[index.row()];
    switch(role)
    {
        case NameRole:
            job->setName(value.toString());
            break;
        case CompletionRole:
            job->setCompletion(value.toFloat());
            break;
        case StatusRole:
            job->setStatus((Job::StatusType)value.toInt());
            break;
        case ThumbnailRole:
            job->setThumbnail(value.toUrl());
            break;
        default:
            return false;
    }
    emit dataChanged(index, index);
    return true;
}

void JobModel::addJob(Job* job)
{
    beginInsertRows(QModelIndex(), rowCount(), rowCount());

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(job, QQmlEngine::CppOwnership);
    job->setParent(this);

    _jobs << job;
    endInsertRows();

    // model and contained object synchronization
    QModelIndex id = index(rowCount() - 1, 0);
    auto callback = [id, this]() {
        emit dataChanged(id, id);
    };
    connect(job, &Job::nameChanged, this, callback);
    connect(job, &Job::completionChanged, this, callback);
    connect(job, &Job::statusChanged, this, callback);
    connect(job, &Job::thumbnailChanged, this, callback);

    job->selectThumbnail();

    emit countChanged(rowCount());
}

void JobModel::addJob()
{
    Project* project = qobject_cast<Project*>(parent());
    assert(project);
    Job* job = new Job(project);
    addJob(job);
}

void JobModel::duplicateJob(Job* ref)
{
    Project* project = qobject_cast<Project*>(parent());
    assert(project);
    Job* job = new Job(project);
    job->load(*ref);
    addJob(job);
}

void JobModel::removeJob(Job* job)
{
    // ensure that we have at least one job
    if(rowCount() == 1)
    {
        Job* newJob = new Job(job->project());
        addJob(newJob);
    }
    // find and remove the job
    int id = _jobs.indexOf(job);
    if(id < 0)
        return;
    beginRemoveRows(QModelIndex(), id, id);
    _jobs.removeAt(id);
    delete job;
    endRemoveRows();
    emit countChanged(rowCount());
}

QVariantMap JobModel::get(int row) const
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
