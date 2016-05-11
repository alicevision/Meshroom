#pragma once

#include <QQmlApplicationEngine>
#include "models/Scene.hpp"

namespace meshroom
{

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Scene* scene READ scene CONSTANT)

public:
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public:
    Q_SLOT Scene* scene() const { return _scene; }
    Q_SLOT void loadPlugins();

private:
    Scene* _scene;
};

} // namespaces
