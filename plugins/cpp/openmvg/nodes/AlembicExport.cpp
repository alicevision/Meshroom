#include "AlembicExport.hpp"

using namespace dg;

AlembicExport::AlembicExport(std::string nodeName)
    : BaseNode(nodeName, "openMVG_main_ConvertSfM_DataFormat")
{
    registerInput<FileSystemRef>("sfmdata2");

    registerOutput<FileSystemRef>("abc");
}

void AlembicExport::prepare(const std::string& cacheDir,
                           const std::map<std::string, AttributeList>& in,
                           AttributeList& out,
                           std::vector<std::vector<std::string>>& commandsArgs)
{

    // register a new output attribute
    FileSystemRef outRef(cacheDir, "result", ".abc");
    out.emplace_back(make_ptr<Attribute>(outRef));

    commandsArgs.push_back({
                           "-i", in.at("sfmdata2")[0]->toString(),
                           "-o", outRef.toString(), // output .abc file
                           "--INTRINSICS",
                           "--EXTRINSICS",
                           "--STRUCTURE",
                           "--OBSERVATIONS"
                           });
}
