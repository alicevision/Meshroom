#include "Application.hpp"
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
    qmlRegisterType<Shortcut>("Popart", 0, 1, "Shortcut");

    // start the main application
    Application application;
    return qapp.exec();
}
