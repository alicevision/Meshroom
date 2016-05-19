#pragma once

#include <QObject>
#include <QJsonObject>
#include "PluginInterface.hpp"

namespace meshroom
{

class Plugin : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name CONSTANT)
    Q_PROPERTY(QStringList nodeTypes READ nodeTypes CONSTANT)
    Q_PROPERTY(QString version READ version CONSTANT)

public:
    Plugin(QObject* parent, const QJsonObject& metadata, PluginInterface* instance);

public:
    PluginInterface* instance() { return _instance; }
    
public:
    Q_SLOT QString name() const;
    Q_SLOT QStringList nodeTypes() const;
    Q_SLOT QString version() const;

private:
    QJsonObject _metadata;
    PluginInterface* _instance = nullptr;
};

} // namespace
