#pragma once

#include "BaseNode.hpp"

class ExportForMeshing : public BaseNode
{
public:
    ExportForMeshing(std::string nodeName);
    ~ExportForMeshing() = default;

public:
    void prepare(const std::string& cacheDir,
                 const std::map<std::string, AttributeList>& in,
                 AttributeList& out,
                 std::vector<std::vector<std::string>>& commandsArgs) override;
    std::string type() const override { return "openmvg.ExportForMeshing"; }
};
