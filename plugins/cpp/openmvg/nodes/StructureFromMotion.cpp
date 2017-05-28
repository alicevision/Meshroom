#include "StructureFromMotion.hpp"
#include <QDebug>
#include <QFileInfo>

using namespace dg;

StructureFromMotion::StructureFromMotion(std::string nodeName)
    : BaseNode(nodeName, "openMVG_main_IncrementalSfM")
{
    registerInput<FileSystemRef>("sfmdata");
    registerInput<FileSystemRef>("features");
    registerInput<FileSystemRef>("matches");

    registerOutput<FileSystemRef>("sfmdata2");
}

void StructureFromMotion::prepare(const std::string& cacheDir,
                                  const std::map<std::string, AttributeList>& in,
                                  AttributeList& out,
                                  std::vector<std::vector<std::string>>& commandsArgs)
{
    auto& aSfm = in.at("sfmdata")[0];
    auto& aFeat = in.at("features")[0];
    auto& aMatch = in.at("matches")[0];

    FileSystemRef outRef(cacheDir, "sfm_data", ".json");
    out.emplace_back(make_ptr<Attribute>(outRef));

    auto matchDir = QFileInfo(aMatch->toString().c_str()).dir().path().toStdString();
    auto featDir = QFileInfo(aFeat->toString().c_str()).dir().path().toStdString();

    commandsArgs.push_back({
                           "-i", aSfm->toString(),  // input sfm_data file
                           "-F", featDir,           // input feat directory
                           "-m", matchDir,          // input match directory
                           "-o", cacheDir           // output sfm directory
                           });
}
