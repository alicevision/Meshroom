#include "Application.hpp"
#include "gl/GLView.hpp"
#include "models/Job.hpp"
#include "models/Project.hpp"
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
    qmlRegisterType<GLView>("Meshroom.GL", 0, 1, "GLView");
    qmlRegisterType<Job>("Meshroom.Job", 0, 1, "Job");
    qmlRegisterType<Project>("Meshroom.Project", 0, 1, "Project");

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
