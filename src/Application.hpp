#pragma once

#include "models/Scene.hpp"
#include "models/PluginCollection.hpp"
#include "models/NodeCollection.hpp"
#include <QQmlApplicationEngine>
#include <Node.hpp> // dependency_graph

namespace meshroom
{

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Scene* scene READ scene CONSTANT)
    Q_PROPERTY(PluginCollection* plugins READ plugins CONSTANT)
    Q_PROPERTY(NodeCollection* nodes READ nodes CONSTANT)

public:
    Application();
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public:
    Q_SLOT PluginCollection* loadPlugins();
    Q_SLOT Scene* loadScene(const QUrl& url);

public:
    Q_SLOT PluginCollection* plugins() { return &_plugins; }
    Q_SLOT Scene* scene() { return &_scene; }
    Q_SLOT NodeCollection* nodes() { return &_nodes; }
    dg::Ptr<dg::Node> node(const QString& type, const QString& name);

private:
    Scene _scene;
    PluginCollection _plugins;
    NodeCollection _nodes;
};

} // namespaces
