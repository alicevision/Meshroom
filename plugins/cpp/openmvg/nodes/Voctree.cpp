#include "Voctree.hpp"
#include <QFileInfo>

using namespace dg;

Voctree::Voctree(std::string nodeName)
    : BaseNode(nodeName, "openMVG_main_generatePairList")
{
    registerInput<FileSystemRef>("sfmdata");
    registerInput<FileSystemRef>("features");
    registerInput<FileSystemRef>("treeFile");
    registerInput<FileSystemRef>("weightFile");

    registerOutput<FileSystemRef>("pairlist");
}

void Voctree::prepare(const std::string &cacheDir,
                      const std::map<std::string, AttributeList>& in,
                      AttributeList& out,
                      std::vector<std::vector<std::string>>& commandsArgs)
{
    FileSystemRef outRef(cacheDir, "pairList", ".txt");
    out.emplace_back(make_ptr<Attribute>(outRef));

    // Get feature/descriptors folder using first feature attribute
    auto feature = in.at("features")[0]->get<FileSystemRef>();
    auto descDir = QFileInfo(feature.toString().c_str()).dir().path().toStdString();

   commandsArgs.push_back({
                          "-l", descDir,                            // input descriptors directory
                          "-t", in.at("treeFile")[0]->toString(),   // input .tree file
                          "-w", in.at("weightFile")[0]->toString(), // input .weights file
                          "-o", outRef.toString()                   // output pairlist.txt
                          });
}

