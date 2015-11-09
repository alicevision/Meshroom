#pragma once

#include <QAbstractListModel>
#include "models/Step.hpp"

namespace meshroom
{

class StepModel : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum StepRoles
    {
        NameRole = Qt::UserRole + 1,
        AttributesRole,
        ModelDataRole
    };

public:
    StepModel(QObject* parent = 0);
    void addStep(Step* step);
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;

signals:
    void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Step*> _steps;
};

} // namespace
