#pragma once

#include <QAbstractListModel>
#include "models/Log.hpp"

namespace mockup
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

public:
    LogModel(QObject* parent = 0);
    int rowCount(const QModelIndex& parent = QModelIndex()) const;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const;

public slots:
    void addLog(Log* log);

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const;

private:
    QList<Log*> _logs;
};

} // namespace
