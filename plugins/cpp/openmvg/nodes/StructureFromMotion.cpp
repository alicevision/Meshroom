#include "StructureFromMotion.hpp"
#include "PluginToolBox.hpp"
#include <QCommandLineParser>
#include <QDebug>

using namespace std;
using namespace dg;

StructureFromMotion::StructureFromMotion(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sfmdata", *this),
              make_ptr<Plug>(type_index(typeid(FileSystemRef)), "matches", *this)};
    output = make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sfmdata2", *this);
}

vector<Command> StructureFromMotion::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    vector<Command> commands;

    auto cacheDir = environment.get(Environment::Key::CACHE_DIRECTORY);
    auto matchDir = cacheDir + "/matches";
    auto outDir = cacheDir + "/sfm";

    AttributeList attributes;
    for(auto& aSfm : cache.get(plug("sfmdata")))
    {
        auto sfmRef = aSfm->get<FileSystemRef>();

        // register a new output attribute
        FileSystemRef outRef(outDir, "sfm_data", ".json");
        attributes.emplace_back(make_ptr<Attribute>(outRef));

        // build the command line in case this output does not exists
        if(!outRef.exists())
        {
            Command c(
                {
                    "--compute", type(),     // meshroom compute mode
                    "--",                    // node options:
                    "-i", sfmRef.toString(), // input sfm_data file
                    "-m", matchDir,          // input match directory
                    "-o", outDir             // output sfm directory
                },
                environment);
            commands.emplace_back(c);
        }
    }
    cache.set(output, attributes);
    return commands;
}

void StructureFromMotion::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_IncrementalSfM", arguments);
}
