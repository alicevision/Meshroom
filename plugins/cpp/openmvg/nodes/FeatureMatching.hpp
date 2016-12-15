#pragma once

#include <dglib/dg.hpp>

class FeatureMatching : public dg::Node
{
public:
    FeatureMatching(std::string nodeName);
    ~FeatureMatching() = default;

public:
    std::vector<dg::Command> prepare(dg::Cache&, dg::Environment&, bool&) override;
    void compute(const std::vector<std::string>& args) const override;
    std::string type() const override { return "openmvg.FeatureMatching"; }
};
