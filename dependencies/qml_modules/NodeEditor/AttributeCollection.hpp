#pragma once

#include <QAbstractListModel>
#include <QJsonArray>
#include "Attribute.hpp"

namespace nodeeditor
{

class AttributeCollection : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum AttributeRoles
    {
        NameRole = Qt::UserRole + 1,
        KeyRole,
        TooltipRole,
        TypeRole,
        MinRole,
        MaxRole,
        StepRole,
        OptionsRole,
        ValueRole,
        ModelDataRole
    };

public:
    AttributeCollection(QObject* parent = 0);
    AttributeCollection(const AttributeCollection& obj);
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex& index, const QVariant& value, int role) override;
    Attribute* get(const QString& key);

public:
    Q_SLOT void addAttribute(Attribute* attribute);
    Q_SLOT void addAttribute(const QJsonObject& descriptor);
    Q_SLOT QVariantMap get(int row) const;
    Q_SLOT int getID(const QString&) const;
    Q_SLOT QJsonArray serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonArray&);
    Q_SIGNAL void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Attribute*> _attributes;
};

} // namespace
