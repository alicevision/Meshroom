#include "Node.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>
#include <QEventLoop>

namespace meshroom
{

Node::Node(QObject* parent, const QJsonObject& metadata, Plugin* plugin)
    : QObject(parent)
    , _metadata(metadata)
    , _plugin(plugin)
{
}

QString Node::type() const
{
    return _metadata.value("type").toString();
}

QString Node::plugin() const
{
    return _plugin->name();
}

QString Node::version() const
{
    return _plugin->version();
}

} // namespace
