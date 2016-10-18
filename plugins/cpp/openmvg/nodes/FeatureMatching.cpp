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
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "sfmdata", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "features", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "pairlist", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "method", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "matches", *this);
}

vector<Command> FeatureMatching::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;

    // check the 'pairlist' value
    auto pList = plug("pairlist");
    auto aList = cache.attribute(pList);
    if(!cache.exists(aList))
        throw invalid_argument("FeatureMatching: pairList file not found");

    auto pSfm = plug("sfmdata");
    AttributeList list;
    for(auto& aSfm : cache.attributes(pSfm))
    {
        // check the 'sfmdata' value
        if(!cache.exists(aSfm))
            throw invalid_argument("FeatureMatching: sfm_data file not found");

        // register a new output attribute
        auto aOut = make_ptr<Attribute>(cache.root() + "matches/matches.f.bin");
        list.emplace_back(aOut);

        // build the command line in case this output does not exists
        if(!cache.exists(aOut))
        {
            Command c({
                "--compute", type(),            // meshroom compute mode
                "--",                           // node options:
                "-i", cache.location(aSfm),     // input sfm_data file
                "-o", cache.root() + "matches", // output match directory
                "-n", "ANNL2",                  // input method
                "-l", cache.location(aList),    // input pairList file
            });
            commands.emplace_back(c);
        }
    }
    cache.setAttributes(output, list);

    return commands;
}

void FeatureMatching::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_ComputeMatches", arguments);
}
