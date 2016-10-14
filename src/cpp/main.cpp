#include "Application.hpp"
#include "CommandLine.hpp"
#include <QGuiApplication>
#include <QDebug>

int main(int argc, char* argv[])
{
    using namespace meshroom;

    // application settings
    QCoreApplication::setOrganizationName("meshroom");
    QCoreApplication::setOrganizationDomain("meshroom.eu");
    QCoreApplication::setApplicationName("meshroom");
    QCoreApplication::setApplicationVersion("0.1.0");

    // command line parsing
    CommandLine commandLine;
    commandLine.parse(argc, argv);

    try
    {
        switch(commandLine.mode())
        {
            case CommandLine::OPEN_GUI:
            {
                // GUI application
                QGuiApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
                QGuiApplication qapp(argc, argv);
                QQmlApplicationEngine engine;
                Application application(engine);
                application.loadPlugins();
                // start the main event loop
                return qapp.exec();
            }
            case CommandLine::COMPUTE_NODE:
            {
                // non-GUI application
                QCoreApplication qapp(argc, argv);
                Application application;
                application.loadPlugins();
                // create the specified dg Node
                auto dgNode = application.createNode(commandLine.nodeType(), "");
                if(!dgNode)
                    return EXIT_FAILURE;
                // compute the node
                dgNode->compute(commandLine.positionalArguments());
                return EXIT_SUCCESS;
            }
            case CommandLine::COMPUTE_GRAPH:
            {
                // non-GUI application
                QCoreApplication qapp(argc, argv);
                Application application;
                application.loadPlugins();
                // load the scene
                if(!application.loadScene(commandLine.sceneURL()))
                    return EXIT_FAILURE;
                // process the whole graph starting from the specified node, using the right mode
                application.scene()->graph()->startWorker(commandLine.buildMode(), commandLine.nodeName());
            }
        }
    }
    catch(std::exception& e)
    {
        qCritical() << e.what();
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
