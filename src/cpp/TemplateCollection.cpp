#include "TemplateCollection.hpp"
#include <QQmlEngine>

namespace meshroom
{

TemplateCollection::TemplateCollection(QObject* parent)
    : QAbstractListModel(parent)
{
}

int TemplateCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _templates.count();
}

QVariant TemplateCollection::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _templates.count())
        return QVariant();
    Template* tmplt = _templates[index.row()];
    switch(role)
    {
        case NameRole:
            return tmplt->name();
        case UrlRole:
            return tmplt->url();
        case DescriptionRole:
            return tmplt->description();
        case ModelDataRole:
            return QVariant::fromValue(tmplt);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> TemplateCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
    roles[UrlRole] = "url";
    roles[DescriptionRole] = "description";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void TemplateCollection::add(Template* tmplt)
{
    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(tmplt, QQmlEngine::CppOwnership);
    tmplt->setParent(this);

    // insert the new element
    beginInsertRows(QModelIndex(), rowCount(), rowCount());
    _templates << tmplt;
    endInsertRows();

    Q_EMIT countChanged(rowCount());
}

} // namespace
