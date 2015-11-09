#pragma once

#include <QAbstractListModel>
#include "models/Attribute.hpp"

namespace meshroom
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
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex& index, const QVariant& value, int role) override;

public slots:
    void addAttribute(Attribute* attribute);

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Attribute*> _attributes;
};

} // namespace
