#include "VocTree.hpp"
// #include "CommandLine.hpp"
#include <fstream>

using namespace std;
using namespace dg;

VocTree::VocTree(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "features", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "images", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "selection", *this);
}

std::vector<Command> VocTree::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p = plug("features");

    // compute a hash depending on all inputs
    size_t key = cache.key(*this, cache.attributes(p));
    auto attribute = cache.addAttribute(output, key);

    // check if this file exists
    if(!cache.exists(attribute))
    {
        // the file does not exists, so we add commands to build it
        for(auto& input : cache.attributes(p))
        {
            Command c({"-m", "compute", "-t", type(), "-f", cache.location(input), "-o",
                       cache.location(attribute)});
            commands.emplace_back(c);
        }
        // set the precompute flag
        blocking = true;
    }
    else
    {
        // open and process the file
        ifstream infile(cache.location(attribute));
        if(infile.is_open())
        {
            size_t key;
            while(infile >> key)
                cache.addAttribute(output, key);
        }
    }

    return commands;
}

void VocTree::compute(const std::vector<std::string>& arguments) const
{
    // TODO
}
