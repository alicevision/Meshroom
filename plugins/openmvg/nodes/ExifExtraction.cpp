#include "ExifExtraction.hpp"
#include <QCommandLineParser>
#include <QJsonDocument>
#include <QJsonObject>
#include <QFile>
#include <QDebug>
#include <fstream>

using namespace std;
using namespace dg;

ExifExtraction::ExifExtraction(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "images", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "sensorWidthDatabase", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "sfmdata", *this);
}

vector<Command> ExifExtraction::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;

    // check the 'sensorWidthDatabase' value
    auto pDb = plug("sensorWidthDatabase");
    auto aDb = cache.attribute(pDb);
    if(!aDb || !cache.exists(aDb))
        throw invalid_argument("ExifExtraction: unable to read sensorWidthDatabase file");

    // check the 'images' value
    auto pImg = plug("images");
    auto aImgs = cache.attributes(pImg);
    if(aImgs.empty())
        return commands;

    // create a json object (containing a list of all images)
    QJsonObject json;
    QStringList imageList;
    for(auto& input : cache.attributes(pImg))
        imageList.append(QString::fromStdString(cache.location(input)));
    json.insert("resources", QJsonValue::fromVariant(imageList));

    // save this object in a tmp file
    string jsonPath = cache.root() + "image_list.json";
    QFile file(QString::fromStdString(jsonPath));
    if(!file.open(QIODevice::WriteOnly | QIODevice::Text))
        throw invalid_argument("ExifExtraction: unable to write imagelist file");
    QJsonDocument document(json);
    file.write(document.toJson());
    file.close();

    // register a new output attribute
    auto attribute = make_ptr<Attribute>(cache.root() + "sfm_data.json");
    cache.setAttribute(output, attribute);

    // build the command line in case this output does not exists
    if(!cache.exists(attribute))
    {
        Command c(
            {
                "-j", jsonPath,            // input tmp json file
                "-d", cache.location(aDb), // input sensors database
                "-o", cache.root()         // output directory
            },
            "openMVG_main_SfMInit_ImageListing");
        commands.emplace_back(c);
    }
    return commands;
}

void ExifExtraction::compute(const vector<string>& arguments) const
{
    // never reached
}
