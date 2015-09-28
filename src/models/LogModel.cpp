#include "LogModel.hpp"
#include <QQmlEngine>

namespace mockup
{

LogModel::LogModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

int LogModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _logs.count();
}

QVariant LogModel::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _logs.count())
        return QVariant();
    Log* log = _logs[index.row()];
    switch(role)
    {
        case TypeRole:
            return log->type();
        case MessageRole:
            return log->message();
        case ModelDataRole:
            return QVariant::fromValue(log);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> LogModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[TypeRole] = "type";
    roles[MessageRole] = "message";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void LogModel::addLog(Log* log)
{
    beginInsertRows(QModelIndex(), rowCount(), rowCount());

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(log, QQmlEngine::CppOwnership);
    log->setParent(this);

    _logs << log;
    endInsertRows();
    emit countChanged(rowCount());
}

} // namespace
