#pragma once

#include <QAbstractListModel>
#include "Attribute.hpp"

namespace nodeeditor
{

class AttributeModel : public QAbstractListModel
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
    AttributeModel(QObject* parent = 0);
    AttributeModel(const AttributeModel& obj);
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex& index, const QVariant& value, int role) override;
    Attribute* get(const QString& key);

public slots:
    void addAttribute(Attribute* attribute);
    QVariantMap get(int row) const;

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Attribute*> _attributes;
};

} // namespace
