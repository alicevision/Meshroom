#include "AlembicExport.hpp"
#include "PluginToolBox.hpp"
#include <QDebug>

using namespace std;
using namespace dg;

AlembicExport::AlembicExport(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sfmdata2", *this)};
    output = make_ptr<Plug>(type_index(typeid(FileSystemRef)), "abc", *this);
}

vector<Command> AlembicExport::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    vector<Command> commands;

    auto outDir = environment.local(Environment::Key::CACHE_DIRECTORY);

    AttributeList attributes;
    for(auto& aSfm : cache.get(plug("sfmdata2")))
    {
        auto sfmRef = aSfm->get<FileSystemRef>();

        // register a new output attribute
        FileSystemRef outRef(outDir, "result", ".abc");
        attributes.emplace_back(make_ptr<Attribute>(outRef));

        // build the command line in case this output does not exists
        if(!outRef.exists())
        {
            Command c({
                "--compute", type(),     // meshroom compute mode
                "--",                    // node options:
                "-i", sfmRef.toString(), // input sfm_data file
                "-o", outRef.toString(), // output .abc file
                "--INTRINSICS",          //
                "--EXTRINSICS",          //
                "--STRUCTURE",           //
                "--OBSERVATIONS"         //
            });
            commands.emplace_back(c);
        }
    }
    cache.set(output, attributes);
    return commands;
}

void AlembicExport::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_ConvertSfM_DataFormat", arguments);
}
