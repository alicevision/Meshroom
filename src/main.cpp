#include "models/ApplicationModel.hpp"
#include "InstantCoding.hpp"
#include "Shortcut.hpp"
#include <QtWidgets/QApplication>
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

    // start the main application
    QQmlApplicationEngine engine;
    ApplicationModel application(engine);
    InstantCoding instantCoding(engine);
    instantCoding.watch("./src/qml");

    return qapp.exec();
}
