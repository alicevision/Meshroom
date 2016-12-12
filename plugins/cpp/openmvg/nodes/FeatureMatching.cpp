#include "FeatureMatching.hpp"
#include "PluginToolBox.hpp"
#include <QCommandLineParser>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QDebug>

using namespace std;
using namespace dg;

FeatureMatching::FeatureMatching(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sfmdata", *this),
              make_ptr<Plug>(type_index(typeid(FileSystemRef)), "features", *this),
              make_ptr<Plug>(type_index(typeid(FileSystemRef)), "pairlist", *this),
              make_ptr<Plug>(type_index(typeid(string)), "method", *this)};
    output = make_ptr<Plug>(type_index(typeid(FileSystemRef)), "matches", *this);
}

vector<Command> FeatureMatching::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    vector<Command> commands;

    auto outDir = environment.get(Environment::Key::CACHE_DIRECTORY) + "/matches";

    // check the 'pairlist' value
    auto aPairList = cache.getFirst(plug("pairlist"));
    if(!aPairList)
        throw invalid_argument("FeatureExtraction: missing pairList attribute");
    auto pairRef = aPairList->get<FileSystemRef>();

    AttributeList attributes;
    for(auto& aSfm : cache.get(plug("sfmdata")))
    {
        auto sfmRef = aSfm->get<FileSystemRef>();

        // register a new output attribute
        FileSystemRef outRef(outDir, "matches", ".f.bin");
        attributes.emplace_back(make_ptr<Attribute>(outRef));

        // build the command line in case this output does not exists
        if(!outRef.exists())
        {
            Command c(
                {
                    "--compute", type(),      // meshroom compute mode
                    "--",                     // node options:
                    "-i", sfmRef.toString(),  // input sfm_data file
                    "-l", pairRef.toString(), // input pairList file
                    "-n", "ANNL2",            // input method
                    "-o", outDir,             // output match directory
                },
                environment);
            commands.emplace_back(c);
        }
    }
    cache.set(output, attributes);

    return commands;
}

void FeatureMatching::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_ComputeMatches", arguments);
}
