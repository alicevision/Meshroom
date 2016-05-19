#pragma once

#include <QQmlApplicationEngine>
#include "models/Scene.hpp"
#include "models/PluginCollection.hpp"
#include "models/NodeCollection.hpp"

namespace meshroom
{

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Scene* scene READ scene CONSTANT)
    Q_PROPERTY(PluginCollection* plugins READ plugins CONSTANT)
    Q_PROPERTY(NodeCollection* nodes READ nodes CONSTANT)

public:
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public:
    Q_SLOT void load();
    Q_SLOT Scene* scene() { return &_scene; }
    Q_SLOT PluginCollection* plugins() { return &_plugins; }
    Q_SLOT NodeCollection* nodes() { return &_nodes; }

private:
    Scene _scene;
    PluginCollection _plugins;
    NodeCollection _nodes;
};

} // namespaces
