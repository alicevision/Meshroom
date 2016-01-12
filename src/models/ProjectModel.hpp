#pragma once

#include <QAbstractListModel>
#include "models/Project.hpp"

namespace meshroom
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
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex& index, const QVariant& value, int role) override;

public slots:
    void addProject(Project* project);
    void addProject(const QUrl& url);
    void removeProject(Project* project);
    QVariantMap get(int row);

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Project*> _projects;
};

} // namespace
