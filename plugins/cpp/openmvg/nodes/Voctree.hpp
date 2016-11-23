#pragma once

#include <dglib/dg.hpp>

class Voctree : public dg::Node
{
public:
    Voctree(std::string nodeName);

public:
    std::vector<dg::Command> prepare(dg::Cache&, dg::Environment&, bool&) override;
    void compute(const std::vector<std::string>& args) const override;
    std::string type() const override { return "Voctree"; }
};
