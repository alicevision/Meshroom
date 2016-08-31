#include "LogModel.hpp"
#include "Singleton.hpp"
#include <QQmlEngine>

namespace logger
{

LogModel::LogModel(QObject* parent)
    : QAbstractListModel(parent)
{
    S::getInstance().registerLogger(this);
    connect(this, SIGNAL(addLog(Log*)), this, SLOT(onAddLog(Log*)), Qt::QueuedConnection);
}

LogModel::~LogModel()
{
    clear();
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

void LogModel::onAddLog(Log* log)
{
    beginInsertRows(QModelIndex(), rowCount(), rowCount());
    QQmlEngine::setObjectOwnership(log, QQmlEngine::CppOwnership);
    _logs << log;
    endInsertRows();
    Q_EMIT countChanged(rowCount());
}

void LogModel::clear()
{
    beginRemoveRows(QModelIndex(), 0, rowCount() - 1);
    while(!_logs.isEmpty())
        delete _logs.takeFirst();
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
}

} // namespace
