#include "PluginNode.hpp"
#include <QJsonObject>

namespace meshroom
{

PluginNode::PluginNode(QObject* parent, const QJsonObject& metadata, Plugin* plugin)
    : QObject(parent)
    , _metadata(metadata)
    , _plugin(plugin)
{
}

QString PluginNode::type() const
{
    return _metadata.value("type").toString();
}

QString PluginNode::plugin() const
{
    return _plugin->name();
}

QString PluginNode::version() const
{
    return _plugin->version();
}

} // namespace
