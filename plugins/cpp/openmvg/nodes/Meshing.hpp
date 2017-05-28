#pragma once

#include "BaseNode.hpp"

class Meshing : public BaseNode
{
public:
    Meshing(std::string nodeName);
    ~Meshing() = default;

public:
    void prepare(const std::string& cacheDir,
                 const std::map<std::string, AttributeList>& in,
                 AttributeList& out,
                 std::vector<std::vector<std::string>>& commandsArgs) override;
    std::string type() const override { return "openmvg.Meshing"; }
};
