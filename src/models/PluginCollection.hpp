#pragma once

#include <QAbstractListModel>
#include <QJsonArray>
#include "Plugin.hpp"

namespace meshroom
{

class PluginCollection : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum PluginRoles
    {
        NameRole = Qt::UserRole + 1,
        NodeTypesRole,
        VersionRole,
        ModelDataRole
    };

public:
    PluginCollection(QObject* parent = 0);
    PluginCollection(const PluginCollection& obj) = delete;
    PluginCollection& operator=(PluginCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex&, int role = Qt::DisplayRole) const override;

public:
    Q_SLOT void addPlugin(Plugin*);
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Plugin*> _plugins;
};

} // namespace
