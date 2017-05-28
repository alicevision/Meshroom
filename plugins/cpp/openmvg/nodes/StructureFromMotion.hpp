#pragma once

#include "BaseNode.hpp"

using namespace dg;

class StructureFromMotion : public BaseNode
{
public:
    StructureFromMotion(std::string nodeName);
    ~StructureFromMotion() = default;

public:
    void prepare(const std::string& cacheDir,
                 const std::map<std::string, AttributeList>& in,
                 AttributeList& out,
                 std::vector<std::vector<std::string>>& commandsArgs) override;
    std::string type() const override { return "openmvg.StructureFromMotion"; }
};
