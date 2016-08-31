#pragma once

#include <QAbstractListModel>
#include <QJsonArray>
#include "PluginNode.hpp"

namespace meshroom
{

class PluginNodeCollection : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum PluginNodeRoles
    {
        TypeRole = Qt::UserRole + 1,
        PluginRole,
        VersionRole,
        ModelDataRole
    };

public:
    PluginNodeCollection(QObject* parent = 0);
    PluginNodeCollection(const PluginNodeCollection& obj) = delete;
    PluginNodeCollection& operator=(PluginNodeCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex&, int role = Qt::DisplayRole) const override;
    PluginNode* get(const QString& type);
    void add(PluginNode*);

public:
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<PluginNode*> _nodes;
};

} // namespace
