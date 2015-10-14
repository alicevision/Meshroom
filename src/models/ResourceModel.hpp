#pragma once

#include <QAbstractListModel>
#include "models/Resource.hpp"

namespace meshroom
{

class ResourceModel : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum ResourceRoles
    {
        UrlRole = Qt::UserRole + 1,
        NameRole,
        ModelDataRole
    };

public:
    ResourceModel(QObject* parent = 0);
    int rowCount(const QModelIndex& parent = QModelIndex()) const;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const;

public slots:
    void addResource(Resource* resource);
    void addResource(const QUrl& url);
    void removeResource(Resource* resource);

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const;

private:
    QList<Resource*> _resources;
};

} // namespace
