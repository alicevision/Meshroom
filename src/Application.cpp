#include "Application.hpp"
#include "io/SettingsIO.hpp"
#include <QCoreApplication>
#include <QtQml/QQmlContext>

namespace meshroom
{

Application::Application(QQmlApplicationEngine& engine)
    : QObject(nullptr)
    , _scenes(new SceneModel(this))
    , _proxy(new QSortFilterProxyModel(this))
{
    // setup proxy filters
    _proxy->setSourceModel(_scenes);
    _proxy->setFilterRole(SceneModel::NameRole);

    // initialize recent scene lists
    SettingsIO::loadRecentScenes(_scenes);

    // expose this object to QML & load the main QML file
    if(engine.rootContext())
        engine.rootContext()->setContextProperty("_application", this);

    engine.load(QCoreApplication::applicationDirPath() + "/qml/main.qml");
}

} // namespace
