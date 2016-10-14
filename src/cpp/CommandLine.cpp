#include "CommandLine.hpp"
#include <QDebug>

namespace // empty namespace
{

const char* application_opt = R"(
Examples:

    meshroom
    meshroom --help
    meshroom --version

    compute mode:
        meshroom --compute NodeType --help
        meshroom --compute NodeType -- --nodeArg1 --nodeArg2

    compute-graph mode:
        meshroom --compute-graph scene.meshroom --help
        meshroom --compute-graph scene.meshroom --local
        meshroom --compute-graph scene.meshroom --tractor
        meshroom --compute-graph scene.meshroom --node nodeName --tractor)";

const char* compute_opt = R"(Compute a particular node.)";
const char* computegraph_opt = R"(Compute the whole graph.)";
const char* local_opt = R"([-g mode] Run locally. (default))";
const char* tractor_opt = R"([-g mode] Run through Tractor.)";
const char* node_opt = R"([-g mode] Start the graph traversal from this particular node.)";

} // empty namespace

namespace meshroom
{

CommandLine::CommandLine()
{
    _parser.addHelpOption();
    _parser.addVersionOption();
    _parser.addOptions({
        {{"c", "compute"}, compute_opt, "node-type"},
        {{"g", "compute-graph"}, computegraph_opt, "meshroom-file"},
    });
    _parser.setSingleDashWordOptionMode(QCommandLineParser::ParseAsLongOptions);
    _parser.setApplicationDescription(application_opt);
}

void CommandLine::parse(int& argc, char** argv)
{
    // to qList
    QStringList arguments;
    for(auto i = 0; i < argc; ++i)
        arguments.append(argv[i]);

    // parse (no builtin options / error handling)
    _parser.parse(arguments);

    // add mode-specific options
    if(_parser.isSet("c"))
    {
        _mode = COMPUTE_NODE;
        _parser.addPositionalArgument("node-options",
                                      "[-c mode] Options needed to compute the specified node.",
                                      "-- [node-options...]");
    }
    else if(_parser.isSet("g"))
    {
        _mode = COMPUTE_GRAPH;
        _parser.addOptions({
            {{"l", "local"}, local_opt},
            {{"t", "tractor"}, tractor_opt},
            {{"n", "node"}, node_opt, "node-name"},
        });
    }
    else
    {
        _mode = OPEN_GUI;
    }

    // parse (with builtin options & error handling)
    QCoreApplication qapp(argc, argv);
    _parser.process(qapp);
}

std::vector<std::string> CommandLine::positionalArguments() const
{
    std::vector<std::string> arguments;
    for(auto arg : _parser.positionalArguments())
        arguments.emplace_back(arg.toStdString());
    return arguments;
}

QUrl CommandLine::sceneURL() const
{
    return QUrl::fromLocalFile(_parser.value("compute-graph"));
}

Graph::BuildMode CommandLine::buildMode() const
{
    if(_parser.isSet("tractor"))
        return Graph::BuildMode::COMPUTE_TRACTOR;
    return Graph::BuildMode::COMPUTE_LOCAL;
}

} // namespace
