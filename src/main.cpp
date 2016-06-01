#include "Application.hpp"
#include "CommandLine.hpp"
#include <QtWidgets/QApplication>
#include <QDebug>

int main(int argc, char* argv[])
{
    using namespace meshroom;

    QApplication qapp(argc, argv);

    // application settings
    QCoreApplication::setOrganizationName("meshroom");
    QCoreApplication::setOrganizationDomain("meshroom.eu");
    QCoreApplication::setApplicationName("meshroom");
    QCoreApplication::setApplicationVersion("0.1.0");

    // command line parsing
    CommandLine commandLine;
    commandLine.parse();

    try
    {
        switch(commandLine.mode())
        {
            case CommandLine::OPEN_GUI:
            {
                QQmlApplicationEngine engine;
                Application application(engine);
                application.loadPlugins();
                return qapp.exec();
            }
            case CommandLine::COMPUTE_NODE:
            {
                Application application;
                application.loadPlugins();
                auto dgNode = application.node(commandLine.nodeType(), "");
                if(!dgNode)
                    return EXIT_FAILURE;
                std::vector<std::string> arguments;
                for(auto arg : QCoreApplication::arguments())
                    arguments.emplace_back(arg.toStdString());
                dgNode->compute(arguments);
                return EXIT_SUCCESS;
            }
            case CommandLine::RUN_LOCAL:
            case CommandLine::RUN_TRACTOR:
            {
                Application application;
                application.loadPlugins();
                auto scene = application.loadScene(commandLine.sceneURL());
                if(commandLine.mode() == CommandLine::RUN_LOCAL)
                    scene->graph()->compute(commandLine.nodeName(), Graph::BuildMode::LOCAL);
                else
                    scene->graph()->compute(commandLine.nodeName(), Graph::BuildMode::TRACTOR);
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
    }

    return EXIT_SUCCESS;
}
