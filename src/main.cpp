#include "Application.hpp"
#include "gl/GLView.hpp"
#include "models/Scene.hpp"
#include <QtWidgets/QApplication>
#include <QSurfaceFormat>
#include <QtQml>

int main(int argc, char* argv[])
{
    using namespace meshroom;

    QApplication qapp(argc, argv);
    QCoreApplication::setOrganizationName("meshroom");
    QCoreApplication::setOrganizationDomain("meshroom.eu");
    QCoreApplication::setApplicationName("meshroom");

    // register types
    qmlRegisterType<GLView>("Meshroom.GL", 1, 0, "GLView");
    qmlRegisterType<Scene>("Meshroom.Scene", 1, 0, "Scene");

    // set opengl profile
    QSurfaceFormat fmt = QSurfaceFormat::defaultFormat();
    fmt.setVersion(3, 2);
    fmt.setProfile(QSurfaceFormat::CoreProfile);
    QSurfaceFormat::setDefaultFormat(fmt);

    // start the main application
    QQmlApplicationEngine engine;
    engine.addImportPath(qApp->applicationDirPath() + "/qml_modules");
    Application application(engine);

    return qapp.exec();
}
