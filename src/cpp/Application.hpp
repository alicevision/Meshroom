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

class MeshroomCmd : public QUndoCommand
{
public:
    virtual bool redoImpl() = 0;
    virtual bool undoImpl() = 0;

    void setEnabled(bool enabled) { _enabled = enabled; }

    void redo() override
    {
        if(_enabled)
            redoImpl();
    }

    void undo() override
    {
        if(_enabled)
            undoImpl();
    }

private:
    bool _enabled = true;
};

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

public:
    Scene* scene() { return &_scene; }
    PluginCollection* plugins() { return &_plugins; }
    PluginNodeCollection* pluginNodes() { return &_pluginNodes; }
    TemplateCollection* templates() { return &_templates; }
    QUndoStack* undoStack() { return _undoStack; }
    bool tryAndPushCommand(MeshroomCmd* command);

private:
    Scene _scene;
    PluginCollection _plugins;
    PluginNodeCollection _pluginNodes;
    TemplateCollection _templates;
    QUndoStack* _undoStack;
};

} // namespaces
