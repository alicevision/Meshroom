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
    inputs = {make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sfmdata", *this),
              make_ptr<Plug>(type_index(typeid(FileSystemRef)), "images", *this),
              make_ptr<Plug>(type_index(typeid(float)), "residualError", *this)};
    output = make_ptr<Plug>(type_index(typeid(FileSystemRef)), "poses", *this);
}

vector<Command> Localization::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    vector<Command> commands;

    auto cacheDir = environment.local(Environment::Key::CACHE_DIRECTORY) + "/localization/";
    auto matchDir = environment.local(Environment::Key::CACHE_DIRECTORY) + "/matches/";

    // check the 'sfmdata' value
    Ptr<Attribute> aSfmData = cache.getFirst(plug("sfmdata"));
    if(!aSfmData)
        throw invalid_argument("Localization: missing sfmdata attribute");
    auto sfmRef = aSfmData->get<FileSystemRef>();

    // check the 'residualError' value
    Ptr<Attribute> aResidualError = cache.getFirst(plug("residualError"));
    if(!aResidualError)
        throw invalid_argument("Localization: missing residualError attribute");

    AttributeList attributes;
    for(auto& aImg : cache.get(plug("images")))
    {
        auto imgRef = aImg->get<FileSystemRef>();

        // register a new output attribute
        auto uid = UID(type(), {aSfmData, aImg});
        auto outDir = cacheDir + to_string(uid);
        FileSystemRef outRef(outDir, "found_pose_centers", ".ply");
        attributes.emplace_back(make_ptr<Attribute>(outRef));

        // add a new comand
        if(!outRef.exists())
        {
            Command c({
                "--compute", type(),              // meshroom compute mode
                "--",                             // node options:
                "-i", sfmRef.toString(),          // - sfmdata file
                "-q", imgRef.toString(),          // - image file
                "-r", aResidualError->toString(), // - residual error
                "-m", matchDir,                   // - matches dir
                "-o", outDir                      // - output dir
            });
            commands.emplace_back(c);
        }
    }
    cache.set(output, attributes);

    return commands;
}

void Localization::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_SfM_Localization", arguments);
}
