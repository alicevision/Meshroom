#include "Localization.hpp"
#include "PluginToolBox.hpp"
#include <QCommandLineParser>
#include <QProcess>
#include <QDebug>

using namespace std;
using namespace dg;

Localization::Localization(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "sfmdata", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "images", *this),
              make_ptr<Plug>(Attribute::Type::FLOAT, "residualError", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "poses", *this);
}

vector<Command> Localization::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;

    Ptr<Attribute> aSfmData = cache.attribute(plug("sfmdata"));
    Ptr<Attribute> aResidualError = cache.attribute(plug("residualError"));

    if(!aSfmData || !cache.exists(aSfmData))
        throw invalid_argument("Localization: sfm_data file not found");

    AttributeList list;
    for(auto& aImage : cache.attributes(plug("images")))
    {
        // compute a unique key
        size_t key = cache.key(*this, {aSfmData, aImage});
        // compute output paths
        string outdir = cache.root() + "localization/" + to_string(key);
        string outfile = outdir + "/found_pose_centers.ply";
        // add a new output attribute
        auto attribute = make_ptr<Attribute>(outfile);
        list.emplace_back(attribute);
        // add a new comand
        if(!cache.exists(attribute))
        {
            Command c({
                "--compute", type(),            // meshroom compute mode
                "--",                           // node options:
                "-i", cache.location(aSfmData), // - sfmdata file
                "-q", cache.location(aImage),   // - image file
                "-r", toString(aResidualError), // - residual error
                "-m", cache.root() + "matches", // - matches dir
                "-o", outdir                    // - output dir
            });
            commands.emplace_back(c);
        }
    }
    cache.setAttributes(output, list);

    return commands;
}

void Localization::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_SfM_Localization", arguments);
}
