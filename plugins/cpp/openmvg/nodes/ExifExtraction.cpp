#include "ExifExtraction.hpp"
#include "PluginToolBox.hpp"
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
    inputs = {make_ptr<Plug>(type_index(typeid(FileSystemRef)), "images", *this),
              make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sensorWidthDatabase", *this)};
    output = make_ptr<Plug>(type_index(typeid(FileSystemRef)), "sfmdata", *this);
}

vector<Command> ExifExtraction::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    vector<Command> commands;

    // check the 'sensorWidthDatabase' value
    auto aDb = cache.getFirst(plug("sensorWidthDatabase"));
    if(!aDb)
        throw invalid_argument("ExifExtraction: missing sensorWidthDatabase value");
    auto dbFile = aDb->get<FileSystemRef>();

    // check the 'images' value
    auto aImgs = cache.get(plug("images"));
    if(aImgs.empty())
        throw invalid_argument("ExifExtraction: empty image list");

    // create a json object containing a list of all images
    QJsonObject json;
    QStringList imageList;
    for(auto& input : aImgs)
        imageList.append(QString::fromStdString(input->toString()));
    json.insert("resources", QJsonValue::fromVariant(imageList));

    // read environment and retrieve the cache directory
    auto outDir = environment.get(Environment::Key::CACHE_DIRECTORY);

    // save this json object in a file
    string jsonPath = outDir + "/image_list.json";
    QFile jsonFile(QString::fromStdString(jsonPath));
    if(!jsonFile.open(QIODevice::WriteOnly | QIODevice::Text))
        throw invalid_argument("ExifExtraction: unable to write imagelist file");
    QJsonDocument document(json);
    jsonFile.write(document.toJson());
    jsonFile.close();

    // register a new output attribute
    FileSystemRef outRef(outDir, "sfm_data", ".json");
    cache.set(output, {make_ptr<Attribute>(outRef)});

    // build the command line in case this output does not exists
    if(!outRef.exists())
    {
        Command c(
            {
                "--compute", type(),     // meshroom compute mode
                "--",                    // node options:
                "-j", jsonPath,          // input tmp json file
                "-d", dbFile.toString(), // input sensors database
                "-o", outDir             // output directory
            },
            environment);
        commands.emplace_back(c);
    }
    return commands;
}

void ExifExtraction::compute(const vector<string>& arguments) const
{
    PluginToolBox::executeProcess("openMVG_main_SfMInit_ImageListing", arguments);
}
