#pragma once

#include <QAbstractListModel>
#include "Log.hpp"

namespace logger
{

class LogModel : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum LogRoles
    {
        TypeRole = Qt::UserRole + 1,
        MessageRole,
        ModelDataRole
    };
    Q_ENUMS(LogRoles)

public:
    LogModel(QObject* parent = 0);
    ~LogModel();

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    Q_SLOT void clear();
    Q_SIGNAL void addLog(Log* log);
    Q_SIGNAL void countChanged(int c);

private:
    Q_SLOT void onAddLog(Log* log);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Log*> _logs;
};

} // namespace
