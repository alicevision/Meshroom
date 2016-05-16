#pragma once

#include <QQmlApplicationEngine>
#include <QJsonObject>
#include "models/Scene.hpp"

namespace meshroom
{

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Scene* scene READ scene CONSTANT)
    Q_PROPERTY(QStringList nodeTypes READ nodeTypes WRITE setNodeTypes NOTIFY nodeTypesChanged)
    Q_PROPERTY(QVariantMap nodeDescriptors READ nodeDescriptors WRITE setNodeDescriptors
                   NOTIFY nodeDescriptorsChanged)

public:
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public:
    Q_SLOT Scene* scene() const { return _scene; }
    Q_SLOT QStringList nodeTypes() const { return _nodeTypes; }
    Q_SLOT QVariantMap nodeDescriptors() const { return _nodeDescriptors; }
    Q_SLOT void setNodeTypes(const QStringList&);
    Q_SLOT void setNodeDescriptors(const QVariantMap&);
    Q_SIGNAL void nodeTypesChanged();
    Q_SIGNAL void nodeDescriptorsChanged();

public:
    Q_SLOT void loadPlugins();

private:
    Scene* _scene;
    QStringList _nodeTypes;
    QVariantMap _nodeDescriptors;
};

} // namespaces
