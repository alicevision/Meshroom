#pragma once

#include <dglib/dg.hpp>

class ImageListing : public dg::Node
{
public:
    ImageListing(std::string nodeName);

public:
    std::vector<dg::Command> prepare(dg::Cache&, dg::Environment&, bool&) override;
    void compute(const std::vector<std::string>& args) const override;
    std::string type() const override { return "openmvg.ImageListing"; }
};
