#include "ImageListing.hpp"
#include <QDebug>

using namespace dg;

const std::vector<std::string> ImageListing::IMAGES_EXT = {"JPG", "JPEG", "PNG"};

ImageListing::ImageListing(std::string nodeName)
    : BaseNode(nodeName, "")
{
    registerInput<FileSystemRef>("files");

    registerOutput<FileSystemRef>("images");
}

void ImageListing::prepare(const std::string& cacheDir,
                           const std::map<std::string, AttributeList>& in,
                           AttributeList& out,
                           std::vector<std::vector<std::string>>& commandsArgs)
{
    for(auto& aFile : in.at("files"))
    {
        FileSystemRef file(aFile->get<FileSystemRef>());
        if(std::find(IMAGES_EXT.begin(), IMAGES_EXT.end(), file.extension()) != IMAGES_EXT.end())
            out.emplace_back(aFile);
    }
}
