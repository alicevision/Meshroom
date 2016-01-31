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
    ResourceModel(QObject* parent, const ResourceModel& obj);
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;

public slots:
    void addResource(Resource* resource);
    void addResource(const QUrl& url);
    void removeResource(Resource* resource);
    QVariantMap get(int row) const;

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Resource*> _resources;
};

} // namespace
