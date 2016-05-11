#pragma once

#include <QQmlApplicationEngine>
#include "models/Scene.hpp"

namespace meshroom
{

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Scene* scene READ scene CONSTANT)
    Q_PROPERTY(QStringList nodeTypes READ nodeTypes WRITE setNodeTypes NOTIFY nodeTypesChanged)

public:
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public:
    Q_SLOT Scene* scene() const { return _scene; }
    Q_SLOT QStringList nodeTypes() const { return _nodeTypes; }
    Q_SLOT void setNodeTypes(const QStringList&);
    Q_SLOT void loadPlugins();
    Q_SIGNAL void nodeTypesChanged();

private:
    Scene* _scene;
    QStringList _nodeTypes;
};

} // namespaces
