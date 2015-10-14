#include "StepModel.hpp"
#include <QQmlEngine>

namespace meshroom
{

StepModel::StepModel(QObject* parent)
    : QAbstractListModel(parent)
{
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

} // namespace
