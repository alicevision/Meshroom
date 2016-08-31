#pragma once

#include "Scene.hpp"
#include "PluginCollection.hpp"
#include "PluginNodeCollection.hpp"
#include <QQmlApplicationEngine>
#include <dglib/dg.hpp>

namespace meshroom
{

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Scene* scene READ scene CONSTANT)
    Q_PROPERTY(PluginCollection* plugins READ plugins CONSTANT)
    Q_PROPERTY(PluginNodeCollection* pluginNodes READ pluginNodes CONSTANT)

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
    Q_SLOT PluginNodeCollection* pluginNodes() { return &_pluginNodes; }
    dg::Ptr<dg::Node> node(const QString& type, const QString& name);

private:
    Scene _scene;
    PluginCollection _plugins;
    PluginNodeCollection _pluginNodes;
};

} // namespaces
