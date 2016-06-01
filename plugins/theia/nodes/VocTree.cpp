#include "VocTree.hpp"
// #include "CommandLine.hpp"
#include <fstream>

using namespace std;
using namespace dg;

VocTree::VocTree(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::PATH, "features", *this),
              make_ptr<Plug>(Attribute::Type::PATH, "images", *this)};
    output = make_ptr<Plug>(Attribute::Type::PATH, "selection", *this);
}

std::vector<Command> VocTree::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p = plug("features");

    // compute a hash depending on all inputs
    size_t hash = cache.reserve(*this, cache.slots(p));

    // check if this file exists
    if(!cache.exists(hash))
    {
        // the file does not exists, so we add commands to build it
        for(auto& input : cache.slots(p))
        {
            Command c({"-m", "compute", "-t", type(), "-f", to_string(input->key), "-o",
                       cache.location(hash)});
            commands.emplace_back(c);
        }
        // set the precompute flag
        blocking = true;
    }
    else
    {
        // open and process the file
        ifstream infile(cache.location(hash));
        if(infile.is_open())
        {
            size_t key;
            while(infile >> key)
                cache.reserve(*this, key);
        }
    }

    return commands;
}

void VocTree::compute(const std::vector<std::string>& arguments) const
{
    // TODO
}
