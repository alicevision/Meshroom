#pragma once

#include <QAbstractListModel>
#include "Template.hpp"

namespace meshroom
{

class TemplateCollection : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum TemplateRoles
    {
        NameRole = Qt::UserRole + 1,
        UrlRole,
        DescriptionRole,
        ModelDataRole
    };
    Q_ENUMS(TemplateRoles)

public:
    TemplateCollection(QObject* parent = 0);
    TemplateCollection(const TemplateCollection& obj) = delete;
    TemplateCollection& operator=(TemplateCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex&, int role = Qt::DisplayRole) const override;
    void add(Template*);

public:
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Template*> _templates;
};

} // namespace
