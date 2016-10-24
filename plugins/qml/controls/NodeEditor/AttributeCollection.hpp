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
    Q_ENUMS(AttributeRoles)

public:
    AttributeCollection(QObject* parent = 0);
    AttributeCollection(const AttributeCollection& obj) = delete;
    AttributeCollection& operator=(AttributeCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex& index, const QVariant& value, int role) override;

public:
    Q_SLOT bool add(Attribute*);
    Q_SLOT bool remove(Attribute*);
    Q_SLOT void clear();
    Q_SLOT int rowIndex(Attribute*) const;
    Q_SLOT int rowIndex(const QString&) const;
    Q_SLOT QJsonArray serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonArray&);
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Attribute*> _attributes;
};

inline AttributeCollection::AttributeCollection(QObject* parent)
    : QAbstractListModel(parent)
{
}

inline int AttributeCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _attributes.count();
}

inline QVariant AttributeCollection::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _attributes.count())
        return QVariant();
    Attribute* attribute = _attributes[index.row()];
    switch(role)
    {
        case NameRole:
            return attribute->name();
        case TooltipRole:
            return attribute->tooltip();
        case KeyRole:
            return attribute->key();
        case TypeRole:
            return attribute->type();
        case MinRole:
            return attribute->min();
        case MaxRole:
            return attribute->max();
        case StepRole:
            return attribute->step();
        case OptionsRole:
            return attribute->options();
        case ValueRole:
            return attribute->value();
        case ModelDataRole:
            return QVariant::fromValue(attribute);
        default:
            return QVariant();
    }
}

inline bool AttributeCollection::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if(index.row() < 0 || index.row() >= _attributes.count() || role != ValueRole)
        return false;
    Attribute* att = _attributes[index.row()];
    if(att->value() == value)
        return false;
    att->setValue(value);
    Q_EMIT dataChanged(index, index);
    return true;
}

inline bool AttributeCollection::add(Attribute* attribute)
{
    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(attribute, QQmlEngine::CppOwnership);
    attribute->setParent(this);

    // insert the new element
    beginInsertRows(QModelIndex(), rowCount(), rowCount());
    _attributes << attribute;
    endInsertRows();

    // handle model and contained object synchronization
    QModelIndex id = index(rowCount() - 1, 0);
    auto callback = [id, this]()
    {
        Q_EMIT dataChanged(id, id);
    };
    connect(attribute, &Attribute::valueChanged, this, callback);

    Q_EMIT countChanged(rowCount());
    return true;
}

inline bool AttributeCollection::remove(Attribute* attribute)
{
    int id = rowIndex(attribute);
    if(id < 0)
        return false;
    beginRemoveRows(QModelIndex(), id, id);
    delete _attributes.takeAt(id);
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
    return true;
}

inline void AttributeCollection::clear()
{
    beginRemoveRows(QModelIndex(), 0, rowCount() - 1);
    while(!_attributes.isEmpty())
        delete _attributes.takeFirst();
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
}

inline int AttributeCollection::rowIndex(Attribute* attribute) const
{
    return _attributes.indexOf(attribute);
}

inline int AttributeCollection::rowIndex(const QString& key) const
{
    auto validator = [&](Attribute* a) -> bool
    {
        return a->key() == key;
    };
    auto it = std::find_if(_attributes.begin(), _attributes.end(), validator);
    return (it == _attributes.end()) ? -1 : std::distance(_attributes.begin(), it);
}

inline QJsonArray AttributeCollection::serializeToJSON() const
{
    QJsonArray array;
    for(auto a : _attributes)
        array.append(a->serializeToJSON());
    return array;
}

inline void AttributeCollection::deserializeFromJSON(const QJsonArray& array)
{
    for(auto a : array)
    {
        Attribute* attribute = new Attribute;
        attribute->deserializeFromJSON(a.toObject());
        add(attribute);
    }
}

inline QHash<int, QByteArray> AttributeCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
    roles[TooltipRole] = "tooltip";
    roles[KeyRole] = "key";
    roles[TypeRole] = "type";
    roles[MinRole] = "min";
    roles[MaxRole] = "max";
    roles[StepRole] = "step";
    roles[OptionsRole] = "options";
    roles[ValueRole] = "value";
    roles[ModelDataRole] = "modelData";
    return roles;
}

} // namespace
