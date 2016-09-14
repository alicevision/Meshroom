#include "Application.hpp"
#include "CommandLine.hpp"
#include <QtWidgets/QApplication>
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
                // using a QML engine
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
                std::vector<std::string> arguments;
                for(auto arg : QCoreApplication::arguments())
                    arguments.emplace_back(arg.toStdString());
                dgNode->compute(arguments);
                return EXIT_SUCCESS;
            }
            case CommandLine::RUN_LOCAL:
            case CommandLine::RUN_TRACTOR:
            {
                // non-GUI application
                QCoreApplication qapp(argc, argv);
                Application application;
                application.loadPlugins();
                // load the scene
                auto scene = application.loadScene(commandLine.sceneURL());
                // process the whole graph starting from the specified node, using the right mode
                scene->graph()->startWorker((commandLine.mode() == CommandLine::RUN_LOCAL)
                                                ? Graph::BuildMode::COMPUTE_LOCAL
                                                : Graph::BuildMode::COMPUTE_TRACTOR,
                                            commandLine.nodeName());
            }
            case CommandLine::QUIT_SUCCESS:
                return EXIT_SUCCESS;
            case CommandLine::QUIT_FAILURE:
                return EXIT_FAILURE;
        }
    }
    catch(std::exception& e)
    {
        qCritical() << e.what();
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
