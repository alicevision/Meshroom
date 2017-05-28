#pragma once

#include "BaseNode.hpp"

class ImageListing : public BaseNode
{
public:
    ImageListing(std::string nodeName);

public:
    void prepare(const std::string& cacheDir,
                 const std::map<std::string, AttributeList>& in,
                 AttributeList& out,
                 std::vector<std::vector<std::string>>& commandsArgs) override;
    std::string type() const override { return "openmvg.ImageListing"; }

private:
    static const std::vector<std::string> IMAGES_EXT;
};
