#include "AlembicExport.hpp"
#include "PluginToolBox.hpp"
#include <QDebug>

using namespace std;
using namespace dg;

AlembicExport::AlembicExport(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "sfmdata2", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "abc", *this);
}

vector<Command> AlembicExport::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;

    AttributeList list;
    auto pSfm = plug("sfmdata2");
    for(auto& aSfm : cache.attributes(pSfm))
    {
        // check the 'sfmdata2' value
        if(!cache.exists(aSfm))
            throw invalid_argument("AlembicExport: sfm_data file not found");

        // register a new output attribute
        auto aOut = make_ptr<Attribute>(cache.root() + "result.abc");
        list.emplace_back(aOut);

        // build the command line in case this output does not exists
        if(!cache.exists(aOut))
        {
            Command c({
                "--compute", type(),        // meshroom compute mode
                "--",                       // node options:
                "-i", cache.location(aSfm), // input sfm_data file
                "-o", cache.location(aOut), // output .abc file
                "--INTRINSICS",             //
                "--EXTRINSICS",             //
                "--STRUCTURE",              //
                "--OBSERVATIONS"            //
            });
            commands.emplace_back(c);
        }
    }
    cache.setAttributes(output, list);
    return commands;
}

void AlembicExport::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_ConvertSfM_DataFormat", arguments);
}
