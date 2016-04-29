#pragma once

#include <QQmlApplicationEngine>
#include "models/SceneModel.hpp"
#include <QSortFilterProxyModel>

namespace meshroom
{

class Application : public QObject
{
    Q_OBJECT
    Q_PROPERTY(SceneModel* scenes READ scenes CONSTANT)
    Q_PROPERTY(QSortFilterProxyModel* proxy READ proxy CONSTANT)

public:
    Application(QQmlApplicationEngine& engine);
    ~Application() = default;

public:
    Q_SLOT SceneModel* scenes() const { return _scenes; }
    Q_SLOT QSortFilterProxyModel* proxy() const { return _proxy; }

private:
    SceneModel* _scenes;
    QSortFilterProxyModel* _proxy;
};

} // namespaces
