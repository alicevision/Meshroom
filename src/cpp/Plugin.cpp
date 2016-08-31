#include "Plugin.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>
#include <QEventLoop>

namespace meshroom
{

Plugin::Plugin(QObject* parent, const QJsonObject& metadata, PluginInterface* instance)
    : QObject(parent)
    , _metadata(metadata)
    , _instance(instance)
{
    qInfo() << "new plugin:" << name();
}

QString Plugin::name() const
{
    return _metadata.value("name").toString();
}

QStringList Plugin::nodeTypes() const
{
    QStringList typeList;
    QJsonArray nodes = _metadata.value("nodes").toArray();
    for(auto n : nodes)
        typeList.append(n.toObject().value("type").toString());
    return typeList;
}

QString Plugin::version() const
{
    QJsonObject version = _metadata.value("version").toObject();
    return QString("v%1.%2.%3")
        .arg(version.value("major").toInt())
        .arg(version.value("minor").toInt())
        .arg(version.value("debug").toInt());
}

} // namespace
