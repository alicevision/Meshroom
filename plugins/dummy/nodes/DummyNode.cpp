#include "DummyNode.hpp"

using namespace std;
using namespace dg;

DummyNode::DummyNode(string nodeName)
    : Node(nodeName)
{
    output = make_ptr<Plug>(Attribute::Type::PATH, "output", *this);
    inputs = {make_ptr<Plug>(Attribute::Type::PATH, "input1", *this),
              make_ptr<Plug>(Attribute::Type::PATH, "input2", *this)};
}

std::vector<Command> DummyNode::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p1 = plug("input1");
    auto p2 = plug("input2");
    for(auto& input1 : cache.slots(p1))
    {
        for(auto& input2 : cache.slots(p2))
        {
            size_t hash = cache.reserve(*this, {input1, input2});
            if(!cache.exists(hash))
            {
                Command c({cache.location(hash)}, "/usr/bin/touch");
                commands.emplace_back(c);
            }
        }
    }
    return commands;
}
