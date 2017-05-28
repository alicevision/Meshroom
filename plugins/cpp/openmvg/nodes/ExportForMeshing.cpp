#include "ExportForMeshing.hpp"
#include <QDebug>

using namespace dg;

ExportForMeshing::ExportForMeshing(std::string nodeName)
    : BaseNode(nodeName, "openMVG_main_openMVG2CMPMVS2")
{
    registerInput<FileSystemRef>("sfmdata");
    registerInput<std::string>("scale");

    registerOutput<FileSystemRef>("output");
}

void ExportForMeshing::prepare(const std::string& cacheDir,
                               const std::map<std::string, AttributeList>& in,
                               AttributeList& out,
                               std::vector<std::vector<std::string>>& commandsArgs)
{
    FileSystemRef iniFile(cacheDir, "mvs", ".ini");
    out.emplace_back(make_ptr<Attribute>(iniFile));

    commandsArgs.push_back({
                            "-i", in.at("sfmdata")[0]->toString(),  // input sfm_data file
                            "-s", in.at("scale")[0]->toString(),    // meshing scale
                            "-o", cacheDir                          // output meshing directory
                           });
}
