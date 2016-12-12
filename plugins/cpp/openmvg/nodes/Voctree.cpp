#include "Voctree.hpp"
#include "PluginToolBox.hpp"
#include <QDebug>

using namespace std;
using namespace dg;

Voctree::Voctree(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sfmdata", *this),
              make_ptr<Plug>(type_index(typeid(FileSystemRef)), "features", *this),
              make_ptr<Plug>(type_index(typeid(FileSystemRef)), "treeFile", *this),
              make_ptr<Plug>(type_index(typeid(FileSystemRef)), "weightFile", *this)};
    output = make_ptr<Plug>(type_index(typeid(FileSystemRef)), "pairlist", *this);
}

vector<Command> Voctree::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    vector<Command> commands;

    auto outDir = environment.get(Environment::Key::CACHE_DIRECTORY);

    // check the 'treeFile' value
    auto aTree = cache.getFirst(plug("treeFile"));
    if(!aTree)
        throw invalid_argument("Voctree: missing treeFile attribute");
    auto treeRef = aTree->get<FileSystemRef>();

    // check the 'weightFile' value
    auto aWeight = cache.getFirst(plug("weightFile"));
    if(!aWeight)
        throw invalid_argument("Voctree: missing weightFile attribute");
    auto weightRef = aWeight->get<FileSystemRef>();

    AttributeList attributes;
    for(auto& aSfm : cache.get(plug("sfmdata")))
    {
        auto sfmRef = aSfm->get<FileSystemRef>();

        // register a new output attribute
        FileSystemRef outRef(outDir, "pairList", ".txt");
        attributes.emplace_back(make_ptr<Attribute>(outRef));

        // build the command line in case this output does not exists
        if(!outRef.exists())
        {
            Command c(
                {
                    "--compute", type(),        // meshroom compute mode
                    "--",                       // node options:
                    "-l", outDir + "/matches",  // input match directory
                    "-t", treeRef.toString(),   // input .tree file
                    "-w", weightRef.toString(), // input .weights file
                    "-o", outRef.toString()     // output pairlist.txt
                },
                environment);
            commands.emplace_back(c);
        }
    }
    cache.set(output, attributes);
    return commands;
}

void Voctree::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_generatePairList", arguments);
}
