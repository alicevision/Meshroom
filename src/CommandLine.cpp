#include "CommandLine.hpp"
#include <QDebug>

namespace
{
const char* mode_opt = R"(Execution mode:
    - e, edit (default, GUI mode)
    - c, compute
    - rl, run-local
    - rt, run-tractor)";

const char* name_opt = R"(Node name:
    Available with -mode=rl or -mode=rt.)";

const char* scene_opt = R"(Scene file:
    Available with -mode=rl or -mode=rt.)";

const char* type_opt = R"(Node type:
    Available with -mode=c.)";
}

namespace meshroom
{

CommandLine::CommandLine()
{
    _parser.addHelpOption();
    _parser.addVersionOption();
    _parser.addOptions({
        {{"m", "mode"}, mode_opt, "mode", "edit"},
        {{"n", "name"}, name_opt, "name"},
        {{"s", "scene"}, scene_opt, "path"},
        {{"t", "type"}, type_opt, "type"},
    });
    _parser.setSingleDashWordOptionMode(QCommandLineParser::ParseAsLongOptions);
}

void CommandLine::parse(int& argc, char** argv)
{
    // options as string list
    QStringList arguments;
    for(auto i = 0; i < argc; ++i)
        arguments.append(argv[i]);

    // command line parsing (ignore unknown options error)
    _parser.parse(arguments);

    if(_parser.isSet("v"))
    {
        qInfo() << qPrintable(QCoreApplication::applicationName())
                << qPrintable(QCoreApplication::applicationVersion());
        _mode = QUIT_SUCCESS;
        return;
    }

    if(_parser.isSet("h"))
    {
        _parser.showHelp();
        _mode = QUIT_SUCCESS;
        return;
    }

    auto toEnum = [](const QString& mode) -> MODE
    {
        if(mode == "edit" || mode == "e")
            return OPEN_GUI;
        if(mode == "compute" || mode == "c")
            return COMPUTE_NODE;
        if(mode == "run-local" || mode == "rl")
            return RUN_LOCAL;
        if(mode == "run-tractor" || mode == "rt")
            return RUN_TRACTOR;
        qCritical() << "unknown mode. Exit";
        return QUIT_FAILURE;
    };

    auto checkOptionValidity = [&](const QString& mode)
    {
        if(_parser.isSet(mode))
            return;
        qCritical() << "missing commandline argument" << qPrintable(QString("--%1").arg(mode));
        _mode = QUIT_FAILURE;
    };

    _mode = toEnum(_parser.value("m"));
    switch(_mode)
    {
        case COMPUTE_NODE:
            checkOptionValidity("type");
            break;
        case RUN_LOCAL:
        case RUN_TRACTOR:
            checkOptionValidity("name");
            checkOptionValidity("scene");
            break;
        default:
            break;
    }
}

} // namespace
