#pragma once

#include <QAbstractListModel>
#include "models/Job.hpp"

namespace meshroom
{

class JobModel : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum JobRoles
    {
        UrlRole = Qt::UserRole + 1,
        NameRole,
        DateRole,
        UserRole,
        CompletionRole,
        StatusRole,
        ThumbnailRole,
        StepsRole,
        ImagesRole,
        ModelDataRole
    };

public:
    JobModel(QObject* parent = 0);
    int rowCount(const QModelIndex& parent = QModelIndex()) const;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const;
    bool setData(const QModelIndex& index, const QVariant& value, int role);

public slots:
    void addJob(Job* job);
    void addJob(const QUrl& projectUrl);

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const;

private:
    QList<Job*> _jobs;
};

} // namespace
