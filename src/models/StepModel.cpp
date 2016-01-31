#include "StepModel.hpp"
#include <QQmlEngine>

namespace meshroom
{

StepModel::StepModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

StepModel::StepModel(QObject* parent, const StepModel& obj)
    : QAbstractListModel(parent)
{
    QHash<int, QByteArray> names = roleNames();
    for(size_t i = 0; i < obj.rowCount(); ++i)
    {
        Step* s = obj.get(i)[names[ModelDataRole]].value<Step*>();
        addStep(new Step(*s));
    }
}

void StepModel::addStep(Step* step)
{
    beginInsertRows(QModelIndex(), rowCount(), rowCount());

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(step, QQmlEngine::CppOwnership);
    step->setParent(this);

    _steps << step;
    endInsertRows();
    emit countChanged(rowCount());
}

int StepModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _steps.count();
}

QVariant StepModel::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _steps.count())
        return QVariant();
    Step* step = _steps[index.row()];
    switch(role)
    {
        case NameRole:
            return step->name();
        case AttributesRole:
            return QVariant::fromValue(step->attributes());
        case ModelDataRole:
            return QVariant::fromValue(step);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> StepModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
    roles[AttributesRole] = "attributes";
    roles[ModelDataRole] = "modelData";
    return roles;
}

QVariantMap StepModel::get(int row) const
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
