#include "StructureFromMotion.hpp"
#include <QCommandLineParser>
#include <QDebug>

using namespace std;
using namespace dg;

StructureFromMotion::StructureFromMotion(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "sfmdata", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "matches", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "sfmdata2", *this);
}

vector<Command> StructureFromMotion::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;

    auto pSfm = plug("sfmdata");
    AttributeList list;
    for(auto& aSfm : cache.attributes(pSfm))
    {
        // check the 'sfmdata' value
        if(!cache.exists(aSfm))
            throw invalid_argument("StructureFromMotion: sfm_data file not found");

        // register a new output attribute
        auto aOut = make_ptr<Attribute>(cache.root() + "sfm/sfm_data.json");
        list.emplace_back(aOut);

        // build the command line in case this output does not exists
        if(!cache.exists(aOut))
        {
            Command c(
                {
                    "-i", cache.location(aSfm),     // input sfm_data file
                    "-m", cache.root() + "matches", // input match directory
                    "-o", cache.root() + "sfm"      // output sfm directory
                },
                "openMVG_main_IncrementalSfM");
            commands.emplace_back(c);
        }
    }
    cache.setAttributes(output, list);
    return commands;
}

void StructureFromMotion::compute(const vector<string>& arguments) const
{
    // never reached
}
