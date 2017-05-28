#include "ExifExtraction.hpp"

#include <QJsonDocument>
#include <QJsonObject>
#include <QFile>

using namespace dg;

ExifExtraction::ExifExtraction(std::string nodeName)
    : BaseNode(nodeName, "openMVG_main_SfMInit_ImageListing")
{
    registerInput<FileSystemRef>("images");
    registerInput<FileSystemRef>("sensorWidthDatabase");
    registerInput<FileSystemRef>("cameraModel");

    registerOutput<FileSystemRef>("sfmdata");
}

void ExifExtraction::prepare(const std::string &cacheDir,
                             const std::map<std::string, AttributeList> &in,
                             AttributeList &out,
                             std::vector<std::vector<std::string>> &commandsArgs)
{
    auto& aImgs = in.at("images");
    auto& aDbFile = in.at("sensorWidthDatabase")[0];
    auto& aCamModel = in.at("cameraModel")[0];

    // -- Save image list in a json file
    // create a json object containing a list of all images
    QJsonObject json;
    QStringList imageList;
    for(auto& input : aImgs)
        imageList.append(QString::fromStdString(input->toString()));
    json.insert("resources", QJsonValue::fromVariant(imageList));

    FileSystemRef imageListFile(cacheDir, "image_list", ".json");
    const std::string jsonPath = imageListFile.toString();
    QFile jsonFile(QString::fromStdString(jsonPath));
    if(!jsonFile.open(QIODevice::WriteOnly | QIODevice::Text))
        throw std::invalid_argument("ExifExtraction: unable to write imagelist file");
    QJsonDocument document(json);
    jsonFile.write(document.toJson());
    jsonFile.close();

    FileSystemRef outRef(cacheDir, "sfm_data", ".json");
    out.emplace_back(make_ptr<Attribute>(outRef));

    std::vector<std::string> args = {
        "-j", jsonPath,            // input tmp json file
        "-d", aDbFile->toString(), // input sensors database
        "-o", cacheDir             // output directory
    };
    if(aCamModel->toString() != "AUTO")
    {
        // Turn cameramodel to lowercase
        std::string cameraModel = aCamModel->toString();
        std::transform(cameraModel.begin(), cameraModel.end(), cameraModel.begin(), ::towlower);
        args.insert(args.end(), {"-c", cameraModel });
    }
    commandsArgs.push_back(args);
}
