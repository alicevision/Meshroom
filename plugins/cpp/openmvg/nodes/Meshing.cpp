#include "Meshing.hpp"
#include <QDebug>

using namespace dg;

Meshing::Meshing(std::string nodeName)
    : BaseNode(nodeName, "CMPMVS")
{
    registerInput<FileSystemRef>("input");
    registerOutput<FileSystemRef>("meshes");
}

void Meshing::prepare(const std::string& cacheDir,
                      const std::map<std::string, AttributeList>& in,
                      AttributeList& out,
                      std::vector<std::vector<std::string>>& commandsArgs)
{
    FileSystemRef meshRef(cacheDir, "mesh", ".obj");
    FileSystemRef texturedMeshRef(cacheDir, "meshAvImgTex", ".obj");

    out.emplace_back(make_ptr<Attribute>(meshRef));
    out.emplace_back(make_ptr<Attribute>(texturedMeshRef));

    commandsArgs.push_back({
                            in.at("input")[0]->toString(),
                            "--all",
                            "--meshOutputDir", cacheDir
                           });
}
