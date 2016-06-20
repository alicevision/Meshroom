#pragma once

#include <QObject>
#include <QJsonObject>
#include "Plugin.hpp"

namespace meshroom
{

class PluginNode : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString type READ type CONSTANT)
    Q_PROPERTY(QString plugin READ plugin CONSTANT)
    Q_PROPERTY(QString version READ version CONSTANT)
    Q_PROPERTY(QJsonObject metadata READ metadata CONSTANT)

public:
    PluginNode(QObject* parent, const QJsonObject& metadata, Plugin* plugin);

public:
    PluginInterface* pluginInstance() const { return _plugin->instance(); }

public:
    Q_SLOT QString type() const;
    Q_SLOT QString plugin() const;
    Q_SLOT QString version() const;
    Q_SLOT QJsonObject metadata() const { return _metadata; }

private:
    QJsonObject _metadata;
    Plugin* _plugin = nullptr;
};

} // namespace
