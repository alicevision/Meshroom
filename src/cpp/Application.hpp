#pragma once

#include "Scene.hpp"
#include "PluginCollection.hpp"
#include "PluginNodeCollection.hpp"
#include "TemplateCollection.hpp"
#include "Settings.hpp"
#include <QQmlApplicationEngine>
#include <dglib/dg.hpp>

namespace meshroom
{

class UndoCommand; // forward declaration

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Scene* scene READ scene CONSTANT)
    Q_PROPERTY(PluginCollection* plugins READ plugins CONSTANT)
    Q_PROPERTY(PluginNodeCollection* pluginNodes READ pluginNodes CONSTANT)
    Q_PROPERTY(TemplateCollection* templates READ templates CONSTANT)
    Q_PROPERTY(Settings* settings READ settings CONSTANT)
    Q_PROPERTY(Scene* templateScene MEMBER _templateScene NOTIFY templateSceneChanged)

public:
    Application();
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public:
    Q_SLOT PluginCollection* loadPlugins();
    Q_SLOT bool loadScene(const QUrl& url);
    dg::Ptr<dg::Node> createNode(const QString& type, const QString& name);

    // TODO: move this in a new class
    /// Open the given template in the template scene
    Q_INVOKABLE void openTemplate(Template *t);
    /// Create a new scene file based on the current template scene
    Q_INVOKABLE void createTemplateScene(const QString& graphName, const QUrl& filename);
    /// Add template graph to the current scene
    Q_INVOKABLE void createTemplateGraph(const QString& graphName);

public:
    Scene* scene() { return &_scene; }
    PluginCollection* plugins() { return &_plugins; }
    PluginNodeCollection* pluginNodes() { return &_pluginNodes; }
    TemplateCollection* templates() { return &_templates; }
    Settings* settings() { return &_settings; }

    Q_SIGNAL void templateSceneChanged();

protected:
    void setTemplateScene(Scene* scene) {
        if(_templateScene != nullptr)
            _templateScene->deleteLater();
        _templateScene = scene;
        Q_EMIT templateSceneChanged();
    }

private:
    PluginCollection _plugins;
    PluginNodeCollection _pluginNodes;
    TemplateCollection _templates;
    Settings _settings;
    Scene _scene;
    Scene* _templateScene;
};

} // namespaces
