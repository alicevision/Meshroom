#pragma once

#include <QAbstractListModel>
#include "models/Project.hpp"

namespace mockup
{

class ProjectModel : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum ProjectRoles
    {
        NameRole = Qt::UserRole + 1,
        UrlRole,
        JobsRole,
        ProxyRole,
        ModelDataRole
    };

public:
    ProjectModel(QObject* parent = 0);
    int rowCount(const QModelIndex& parent = QModelIndex()) const;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const;

public slots:
    void addProject(Project* project);
    void addProject(const QUrl& url);
    void removeProject(Project* project);

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const;

private:
    QList<Project*> _projects;
};

} // namespace
