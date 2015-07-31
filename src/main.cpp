#include "gl/GLView.hpp"
#include "models/ApplicationModel.hpp"
#include "InstantCoding.hpp"
#include "Shortcut.hpp"
#include <QtWidgets/QApplication>
#include <QSurfaceFormat>
#include <QtQml>

int main(int argc, char* argv[])
{
    using namespace mockup;

    QApplication qapp(argc, argv);
    QCoreApplication::setOrganizationName("PopartEU");
    QCoreApplication::setOrganizationDomain("popart.eu");
    QCoreApplication::setApplicationName("qmlgui");

    // register types
    qRegisterMetaType<QtMsgType>("QtMsgType");
    qmlRegisterType<Shortcut>("Popart", 0, 1, "Shortcut");
    qmlRegisterType<GLView>("Popart", 0, 1, "GLView");;

    // set opengl profile
    QSurfaceFormat fmt = QSurfaceFormat::defaultFormat();
    fmt.setVersion(3, 2);
    fmt.setProfile(QSurfaceFormat::CoreProfile);
    QSurfaceFormat::setDefaultFormat(fmt);

    // start the main application
    QQmlApplicationEngine engine;
    ApplicationModel application(engine);
    InstantCoding instantCoding(engine);
    instantCoding.watch("./src/qml");

    return qapp.exec();
}
