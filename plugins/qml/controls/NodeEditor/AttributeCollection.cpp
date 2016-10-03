#include "AttributeCollection.hpp"
#include <QQmlEngine>
#include <QJsonObject>
#include <QDebug>

namespace nodeeditor
{

AttributeCollection::AttributeCollection(QObject* parent)
    : QAbstractListModel(parent)
{
}

int AttributeCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _attributes.count();
}

QVariant AttributeCollection::data(const QModelIndex& index, int role) const
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

bool AttributeCollection::setData(const QModelIndex& index, const QVariant& value, int role)
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

bool AttributeCollection::add(Attribute* attribute)
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

bool AttributeCollection::remove(Attribute* attribute)
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

void AttributeCollection::clear()
{
    beginRemoveRows(QModelIndex(), 0, rowCount() - 1);
    while(!_attributes.isEmpty())
        delete _attributes.takeFirst();
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
}

int AttributeCollection::rowIndex(Attribute* attribute) const
{
    return _attributes.indexOf(attribute);
}

int AttributeCollection::rowIndex(const QString& name) const
{
    int id = 0;
    for(auto a : _attributes)
    {
        if(a->name() == name)
            return id;
        ++id;
    }
    return -1;
}

QVariantMap AttributeCollection::toVMap(int row) const
{
    QHash<int, QByteArray> names = roleNames();
    QHashIterator<int, QByteArray> i(names);
    QVariantMap result;
    while(i.hasNext())
    {
        i.next();
        QModelIndex idx = index(row, 0);
        QVariant data = idx.data(i.key());
        result[i.value()] = data;
    }
    return result;
}

QJsonArray AttributeCollection::serializeToJSON() const
{
    QJsonArray array;
    for(auto a : _attributes)
        array.append(a->serializeToJSON());
    return array;
}

void AttributeCollection::deserializeFromJSON(const QJsonArray& array)
{
    for(auto a : array)
    {
        Attribute* attribute = new Attribute;
        attribute->deserializeFromJSON(a.toObject());
        add(attribute);
    }
}

QHash<int, QByteArray> AttributeCollection::roleNames() const
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
