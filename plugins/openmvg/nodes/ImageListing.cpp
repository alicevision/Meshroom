#include "ImageListing.hpp"
#include <QDebug>

using namespace std;
using namespace dg;

ImageListing::ImageListing(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "files", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "images", *this);
}

vector<Command> ImageListing::prepare(Cache& cache, bool& blocking)
{
    auto file_extension = [](const string& path) -> string
    {
        auto ext = path.substr(path.find_last_of(".") + 1);
        for_each(ext.begin(), ext.end(), [](char& in)
                 {
                     in = ::toupper(in);
                 });
        return ext;
    };

    vector<Command> commands;
    auto pFiles = plug("files");
    AttributeList list;
    for(auto& aFiles : cache.attributes(pFiles))
    {
        auto path = cache.location(aFiles);
        if(file_extension(path) == "JPG")
            list.emplace_back(aFiles);
    }
    cache.setAttributes(output, list);
    return commands;
}

void ImageListing::compute(const vector<string>& arguments) const
{
    // never reached
}
