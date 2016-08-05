#include "FeatureExtraction.hpp"
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
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "sfmdata", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "describerMethod", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "describerPreset", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "features", *this);
}

vector<Command> FeatureExtraction::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;

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

    auto pSfm = plug("sfmdata");
    AttributeList list;
    for(auto& aSfm : cache.attributes(pSfm))
    {
        // check the 'sfmdata' value
        if(!cache.exists(aSfm))
            throw invalid_argument("FeatureExtraction: sfm_data file not found");

        // read the sfm_data json file and retrieve all feat/desc filenames
        bool createCmd = false;
        QJsonObject json = getJSON(cache.location(aSfm));
        for(auto view : json.value("views").toArray())
        {
            int key = view.toObject().value("key").toInt();
            string basename = cache.root() + "matches/" + to_string(key);
            auto aFeat = make_ptr<Attribute>(basename + ".feat");
            auto aDesc = make_ptr<Attribute>(basename + ".desc");
            list.emplace_back(aFeat);
            list.emplace_back(aDesc);
            if(!cache.exists(aFeat) || !cache.exists(aDesc))
                createCmd = true;
        }

        // build the command line in case one feat/desc file does not exists
        if(createCmd)
        {
            Command c(
                {
                    "-i", cache.location(aSfm),    // input sfm_data file
                    "-o", cache.root() + "matches" // output match directory
                },
                "openMVG_main_ComputeFeatures");
            commands.emplace_back(c);
        }
    }
    cache.setAttributes(output, list);

    return commands;
}

void FeatureExtraction::compute(const vector<string>& arguments) const
{
    // never reached
}
