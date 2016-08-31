#pragma once

#include <dglib/dg.hpp>

class StructureFromMotion : public dg::Node
{
public:
    StructureFromMotion(std::string nodeName);
    ~StructureFromMotion() = default;

public:
    std::vector<dg::Command> prepare(dg::Cache&, bool&) override;
    void compute(const std::vector<std::string>& args) const override;
    std::string type() const override { return "StructureFromMotion"; }
};
