#include "JobModel.hpp"
#include <QQmlEngine>

namespace mockup
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
            job->setStatus(value.toInt());
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

    QModelIndex id = index(rowCount() - 1, 0);
    job->setModelIndex(id);
    job->selectThumbnail();
    job->refresh();

    emit countChanged(rowCount());
}

void JobModel::addJob(const QUrl& projectUrl)
{
    QDateTime currentTime = QDateTime::currentDateTime();
    Job* job = new Job(QUrl::fromLocalFile(projectUrl.toLocalFile() + "/reconstructions/" +
                                           currentTime.toString("yyyyMMdd_HHmmss")));
    addJob(job);
}

} // namespace
