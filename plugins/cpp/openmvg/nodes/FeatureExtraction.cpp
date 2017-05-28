#include "FeatureExtraction.hpp"
#include "PluginToolBox.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>


FeatureExtraction::FeatureExtraction(std::string nodeName)
    : BaseNode(nodeName, "openMVG_main_ComputeFeatures")
{
    registerInput<FileSystemRef>("sfmdata");
    // feature/desc files contains the describer type in their name
    registerInput<std::string>("describerMethod", false);
    registerInput<std::string>("describerPreset");

    registerOutput<FileSystemRef>("features");
}

void FeatureExtraction::prepare(const std::string& cacheDir,
                                const std::map<std::string, AttributeList>& in,
                                AttributeList& out,
                                std::vector<std::vector<std::string>>& commandsArgs)
{
    // TODO: get all describer methods
    auto& aSfmData = in.at("sfmdata")[0];
    auto& aDM = in.at("describerMethod")[0];
    auto& aDP = in.at("describerPreset")[0];

    if(!aSfmData->get<FileSystemRef>().exists())
        return;

    QStringList descTypes = QString::fromStdString(aDM->toString()).split(",");
    // read the sfm_data json file and retrieve all feat/desc filenames
    QJsonObject json = PluginToolBox::loadJSON(aSfmData->toString());
    for(auto view : json.value("views").toArray())
    {
        int key = view.toObject().value("key").toInt();
        for(auto& descType : descTypes)
        {
            std::string baseName = std::to_string(key) + "." + descType.toStdString();
            FileSystemRef featref(cacheDir, baseName, ".feat");
            FileSystemRef descref(cacheDir, baseName, ".desc");
            out.emplace_back(make_ptr<Attribute>(featref));
            out.emplace_back(make_ptr<Attribute>(descref));
        }
    }

    // build the command line in case one feat/desc file does not exists
    commandsArgs.push_back({
                            "-i", aSfmData->toString(), // input sfm_data file
                            "-o", cacheDir,             // output match directory
                            "-p", aDP->toString(),      // describer preset
                            "-m", aDM->toString(),      // describer method
                            "-j", "0"                   // number of jobs (0 for automatic mode)
                           });
}
