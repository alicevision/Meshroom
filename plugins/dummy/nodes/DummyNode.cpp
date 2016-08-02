#include "DummyNode.hpp"

using namespace std;
using namespace dg;

DummyNode::DummyNode(string nodeName)
    : Node(nodeName)
{
    output = make_ptr<Plug>(Attribute::Type::STRING, "output", *this);
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "input1", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "input2", *this)};
}

std::vector<Command> DummyNode::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p1 = plug("input1");
    auto p2 = plug("input2");

    for(auto& input1 : cache.attributes(p1))
    {
        for(auto& input2 : cache.attributes(p2))
        {
            size_t key = cache.key(*this, {input1, input2});
            auto attribute = cache.addAttribute(output, key);
            if(!cache.exists(attribute))
            {
                Command c({cache.location(attribute)}, "/usr/bin/touch");
                commands.emplace_back(c);
            }
        }
    }
    return commands;
}
