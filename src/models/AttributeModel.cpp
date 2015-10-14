#include "AttributeModel.hpp"
#include <QQmlEngine>

namespace meshroom
{

AttributeModel::AttributeModel(QObject* parent)
    : QAbstractListModel(parent)
{
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

QHash<int, QByteArray> AttributeModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
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

} // namespace
