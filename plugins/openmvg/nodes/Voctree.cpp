#include "Voctree.hpp"
#include <QDebug>

using namespace std;
using namespace dg;

Voctree::Voctree(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "sfmdata", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "treeFile", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "weightFile", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "pairlist", *this);
}

vector<Command> Voctree::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;

    // check the 'treeFile' value
    auto pTree = plug("treeFile");
    auto aTree = cache.attribute(pTree);
    if(!aTree || !cache.exists(aTree))
        throw invalid_argument("Voctree: unable to read the .tree file");

    // check the 'weightFile' value
    auto pWeight = plug("weightFile");
    auto aWeight = cache.attribute(pWeight);
    if(!aWeight || !cache.exists(aWeight))
        throw invalid_argument("Voctree: unable to read the .weights file");

    auto pSfm = plug("sfmdata");
    AttributeList list;
    for(auto& aSfm : cache.attributes(pSfm))
    {
        // check the 'sfmdata' value
        if(!cache.exists(aSfm))
            throw invalid_argument("Voctree: sfm_data file not found");

        // register a new output attribute
        auto attribute = make_ptr<Attribute>(cache.root() + "pairList.txt");
        list.emplace_back(attribute);

        // build the command line in case this output does not exists
        if(!cache.exists(attribute))
        {
            Command c(
                {
                    "-l", cache.root() + "matches", // input match directory
                    "-t", cache.location(aTree),    // input .tree file
                    "-w", cache.location(aWeight),  // input .weights file
                    "-o", cache.location(attribute) // output pairlist.txt
                },
                "openMVG_main_generatePairList");
            commands.emplace_back(c);
        }
    }
    cache.setAttributes(output, list);

    return commands;
}

void Voctree::compute(const vector<string>& arguments) const
{
    // never reached
}
