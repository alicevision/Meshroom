#include "ApplicationModel.hpp"
#include "io/SettingsIO.hpp"
#include <QCoreApplication>
#include <QtQml/QQmlContext>
#include <iostream>

namespace meshroom
{

ApplicationModel::ApplicationModel(QQmlApplicationEngine& engine)
    : QObject(nullptr)
    , _projects(new ProjectModel(this))
    , _featured(new ResourceModel(this))
{
    // initialize recent and featured project lists
    SettingsIO::loadRecentProjects(_projects);
    SettingsIO::loadFeaturedProjects(_featured);

    // expose this object to QML & load the main QML file
    if(engine.rootContext())
        engine.rootContext()->setContextProperty("_applicationModel", this);
#ifndef NDEBUG
    engine.load("src/qml/main_debug.qml");
#else
    engine.load(QCoreApplication::applicationDirPath() + "/qml/main.qml");
#endif
}

} // namespace
