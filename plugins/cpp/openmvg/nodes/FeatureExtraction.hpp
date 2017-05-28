#pragma once

#include "BaseNode.hpp"

class FeatureExtraction : public BaseNode
{
public:
    FeatureExtraction(std::string nodeName);

public:
    void prepare(const std::string& cacheDir,
                 const std::map<std::string, AttributeList>& in,
                 AttributeList& out,
                 std::vector<std::vector<std::string>>& commandsArgs) override;
    std::string type() const override { return "openmvg.FeatureExtraction"; }
};
