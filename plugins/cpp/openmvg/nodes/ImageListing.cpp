#include "ImageListing.hpp"
#include <QDebug>

using namespace std;
using namespace dg;

ImageListing::ImageListing(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(type_index(typeid(FileSystemRef)), "files", *this)};
    output = make_ptr<Plug>(type_index(typeid(FileSystemRef)), "images", *this);
}

vector<Command> ImageListing::prepare(Cache& cache, Environment& environment, bool& blocking)
{
    AttributeList outputs;
    for(auto& aFile : cache.get(plug("files")))
    {
        FileSystemRef file(aFile->toString());
        if(file.extension() == "JPG")
            outputs.emplace_back(aFile);
    }
    cache.set(output, outputs);

    return vector<Command>(); // nothing to compute
}

void ImageListing::compute(const vector<string>& arguments) const
{
    // never reached
}
