#include "FeatureMatching.hpp"
#include <QFileInfo>

using namespace dg;

FeatureMatching::FeatureMatching(std::string nodeName)
    : BaseNode(nodeName, "openMVG_main_ComputeMatches")
{
    registerInput<FileSystemRef>("sfmdata");
    registerInput<FileSystemRef>("features");
    registerInput<FileSystemRef>("pairlist");
    registerInput<std::string>("method");

    registerOutput<FileSystemRef>("matches");
}

void FeatureMatching::prepare(const std::string& cacheDir,
                                const std::map<std::string, AttributeList>& in,
                                AttributeList& out,
                                std::vector<std::vector<std::string>>& commandsArgs)
{
    auto& aFeatures = in.at("features");

    auto featureFile = aFeatures[0]->get<FileSystemRef>();
    auto featDir = QFileInfo(featureFile.toString().c_str()).dir().path().toStdString();

    QSet<QString> types;
    // Get features describers types based on filenames
    for(auto& feat : aFeatures)
    {
        QString f = QString::fromStdString(feat->toString());
        // aFeatures also contains .desc files, skip them
        if(!f.contains(".feat"))
            continue;
        auto t = f.replace(".feat", "").split(".").back();
        // If the type is already registered, it means that all types are known
        if(types.contains(t))
            break;
        types.insert(t);
    }
    QString descTypes = types.toList().join(",");

    // register a new output attribute
    FileSystemRef outRef(cacheDir, "matches", ".f.bin");
    out.emplace_back(make_ptr<Attribute>(outRef));

    commandsArgs.push_back({
                            "-i", in.at("sfmdata")[0]->toString(),  // input sfm_data file
                            "-m", descTypes.toStdString(),
                            "-l", in.at("pairlist")[0]->toString(), // input pairList file
                            "-n", in.at("method")[0]->toString(),   // nearest matching method
                            "-F", featDir,                          // features directory
                            "-o", cacheDir,                         // output match directory
                           });
}
