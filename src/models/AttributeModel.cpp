#include "AttributeModel.hpp"
#include <QQmlEngine>

namespace meshroom
{

AttributeModel::AttributeModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

AttributeModel::AttributeModel(const AttributeModel& obj)
    : QAbstractListModel(obj.parent())
{
    QHash<int, QByteArray> names = roleNames();
    for(size_t i = 0; i < obj.rowCount(); ++i)
    {
        Attribute* a = obj.get(i)[names[ModelDataRole]].value<Attribute*>();
        addAttribute(new Attribute(*a));
    }
}

int AttributeModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _attributes.count();
}

QVariant AttributeModel::data(const QModelIndex& index, int role) const
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
        case EnabledRole:
            return attribute->enabled();
        default:
            return QVariant();
    }
}

bool AttributeModel::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if(index.row() < 0 || index.row() >= _attributes.count() || role != ValueRole)
        return false;
    Attribute* att = _attributes[index.row()];
    if(att->value() == value)
        return false;
    att->setValue(value);
    emit dataChanged(index, index);
    return true;
}

Attribute* AttributeModel::get(const QString& key)
{
    QListIterator<Attribute*> it(_attributes);
    while(it.hasNext())
    {
        Attribute* a = it.next();
        if(a->key() == key)
            return a;
    }
    return nullptr;
}

QHash<int, QByteArray> AttributeModel::roleNames() const
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
    roles[EnabledRole] = "enabled";
    return roles;
}

void AttributeModel::addAttribute(Attribute* attribute)
{
    beginInsertRows(QModelIndex(), rowCount(), rowCount());

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(attribute, QQmlEngine::CppOwnership);
    attribute->setParent(this);

    _attributes << attribute;
    endInsertRows();
    emit countChanged(rowCount());
}

QVariantMap AttributeModel::get(int row) const
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

} // namespace
