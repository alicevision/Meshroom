#include "FeatureExtraction.hpp"
#include "PluginToolBox.hpp"
#include <QCommandLineParser>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QDebug>

using namespace std;
using namespace dg;

FeatureExtraction::FeatureExtraction(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sfmdata", *this),
              make_ptr<Plug>(type_index(typeid(string)), "describerMethod", *this),
              make_ptr<Plug>(type_index(typeid(string)), "describerPreset", *this)};
    output = make_ptr<Plug>(type_index(typeid(FileSystemRef)), "features", *this);
}

vector<Command> FeatureExtraction::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    vector<Command> commands;

    auto outDir = environment.get(Environment::Key::CACHE_DIRECTORY) + "/matches";

    auto getJSON = [&](const string& path) -> QJsonObject
    {
        // open a file handler
        QString filename = QString::fromStdString(path);
        QFile file(filename);
        if(!file.open(QIODevice::ReadOnly))
            throw invalid_argument("FeatureExtraction: can't open file");
        // read data and close the file handler
        QByteArray data = file.readAll();
        file.close();
        // parse data as JSON
        QJsonParseError error;
        QJsonDocument document(QJsonDocument::fromJson(data, &error));
        if(error.error != QJsonParseError::NoError)
            throw invalid_argument("FeatureExtraction: malformed JSON file");
        return document.object();
    };

    AttributeList outlist;
    for(auto& aSfm : cache.get(plug("sfmdata")))
    {
        // check the 'sfmdata' value
        auto sfmref = aSfm->get<FileSystemRef>();
        if(!sfmref.exists())
        {
            blocking = true;
            return commands;
        }

        // read the sfm_data json file and retrieve all feat/desc filenames
        bool createCmd = false;
        QJsonObject json = getJSON(sfmref.toString());
        for(auto view : json.value("views").toArray())
        {
            int key = view.toObject().value("key").toInt();
            FileSystemRef featref(outDir, to_string(key), ".feat");
            FileSystemRef descref(outDir, to_string(key), ".feat");
            outlist.emplace_back(make_ptr<Attribute>(featref));
            outlist.emplace_back(make_ptr<Attribute>(descref));
            if(!featref.exists() || !descref.exists())
                createCmd = true;
        }

        // build the command line in case one feat/desc file does not exists
        if(createCmd)
        {
            Command c(
                {
                    "--compute", type(),     // meshroom compute mode
                    "--",                    // node options:
                    "-i", sfmref.toString(), // input sfm_data file
                    "-o", outDir,            // output match directory
                    "-j", "0"                // number of jobs (0 for automatic mode)
                },
                environment);
            commands.emplace_back(c);
        }
    }
    cache.set(output, outlist);

    return commands;
}

void FeatureExtraction::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_ComputeFeatures", arguments);
}
