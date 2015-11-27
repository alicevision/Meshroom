#include "gl/GLView.hpp"
#include "models/ApplicationModel.hpp"
#include "util/InstantCoding.hpp"
#include <QtWidgets/QApplication>
#include <QSurfaceFormat>
#include <QtQml>

int main(int argc, char* argv[])
{
    using namespace meshroom;

    QApplication qapp(argc, argv);
    QCoreApplication::setOrganizationName("PopartEU");
    QCoreApplication::setOrganizationDomain("popart.eu");
    QCoreApplication::setApplicationName("meshroom");

    // register types
    qmlRegisterType<GLView>("Popart", 0, 1, "GLView");

    // set opengl profile
    QSurfaceFormat fmt = QSurfaceFormat::defaultFormat();
    fmt.setVersion(3, 2);
    fmt.setProfile(QSurfaceFormat::CoreProfile);
    QSurfaceFormat::setDefaultFormat(fmt);

    // start the main application
    QQmlApplicationEngine engine;
    engine.addImportPath(qApp->applicationDirPath() + "/qml_modules");
    ApplicationModel application(engine);

#ifndef NDEBUG
    InstantCoding instantCoding(engine);
    instantCoding.watch("./src/qml");
#endif

    return qapp.exec();
}
