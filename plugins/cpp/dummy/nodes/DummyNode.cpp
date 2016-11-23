#include "DummyNode.hpp"

using namespace std;
using namespace dg;

DummyNode::DummyNode(string nodeName)
    : Node(nodeName)
{
    output = make_ptr<Plug>(type_index(typeid(string)), "output", *this);
    inputs = {make_ptr<Plug>(type_index(typeid(string)), "input1", *this),
              make_ptr<Plug>(type_index(typeid(string)), "input2", *this)};
}

std::vector<Command> DummyNode::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    vector<Command> commands;
    auto p1 = plug("input1");
    auto p2 = plug("input2");

    for(auto& input1 : cache.get(p1))
    {
        for(auto& input2 : cache.get(p2))
        {
            auto uid = UID(type(), {input1, input2});
            auto outdirectory = environment.local(Environment::Key::CACHE_DIRECTORY);
            auto outfile = FileSystemRef(outdirectory, uid, ".cache");
            cache.push(output, {make_ptr<Attribute>(outfile)});
            if(!outfile.exists())
            {
                Command c({outfile.toString()}, "/usr/bin/touch");
                commands.emplace_back(c);
            }
        }
    }
    return commands;
}
