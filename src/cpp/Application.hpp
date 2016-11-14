#pragma once

#include "Scene.hpp"
#include "PluginCollection.hpp"
#include "PluginNodeCollection.hpp"
#include "TemplateCollection.hpp"
#include <QQmlApplicationEngine>
#include <QUndoStack>
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
    Q_PROPERTY(QObject* undoStack READ undoStack CONSTANT)

public:
    Application();
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public:
    Q_SLOT PluginCollection* loadPlugins();
    Q_SLOT bool loadScene(const QUrl& url);
    dg::Ptr<dg::Node> createNode(const QString& type, const QString& name);
    bool tryAndPushCommand(UndoCommand* command);

public:
    Scene* scene() { return &_scene; }
    PluginCollection* plugins() { return &_plugins; }
    PluginNodeCollection* pluginNodes() { return &_pluginNodes; }
    TemplateCollection* templates() { return &_templates; }
    QUndoStack* undoStack() { return _undoStack; }

private:
    QUndoStack* _undoStack;
    PluginCollection _plugins;
    PluginNodeCollection _pluginNodes;
    TemplateCollection _templates;
    Scene _scene;
};

} // namespaces
