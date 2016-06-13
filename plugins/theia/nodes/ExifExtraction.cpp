#include "ExifExtraction.hpp"
#include <theia/theia.h>
#include <QCommandLineParser>
#include <QDebug>
#include <fstream>

using namespace std;
using namespace dg;

ExifExtraction::ExifExtraction(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::PATH, "images", *this)};
    output = make_ptr<Plug>(Attribute::Type::PATH, "exifs", *this);
}

vector<Command> ExifExtraction::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p = plug("images");
    for(auto& input : cache.slots(p))
    {
        size_t hash = cache.reserve(*this, {input});
        if(!cache.exists(hash))
        {
            Command c({
                "-m", "compute",                  // mode
                "-t", type(),                     // type
                "-i", cache.location(input->key), // input
                "-o", cache.location(hash)        // output
            });
            commands.emplace_back(c);
        }
    }
    return commands;
}

void ExifExtraction::compute(const vector<string>& arguments) const
{
    qDebug() << "[ExifExtraction]";

    // command line options
    QCommandLineParser parser;
    parser.setSingleDashWordOptionMode(QCommandLineParser::ParseAsLongOptions);
    parser.addOptions({
        {{"i", "input"}, "image file", "file"}, {{"o", "output"}, "exif file", "file"},
    });

    // command line parsing
    parser.parse(QCoreApplication::arguments());
    if(!parser.isSet("input") || !parser.isSet("output"))
        throw logic_error("missing command line value");

    string input = parser.value("input").toStdString();
    string output = parser.value("output").toStdString();

    // open a file handler
    ofstream ofs(output);
    if(!ofs.is_open())
        throw logic_error("failed to export exif file");

    // extract EXIF meta data
    theia::ExifReader reader;
    theia::CameraIntrinsicsPrior intrinsics;
    if(!reader.ExtractEXIFMetadata(input, &intrinsics))
        throw logic_error("failed to extract exif metadata");

    // for images with a focal length that was not extracted
    if(!intrinsics.focal_length.is_set)
    {
        // set the focal length based on a median viewing angle
        intrinsics.focal_length.is_set = true;
        intrinsics.focal_length.value =
            1.2 * static_cast<double>(max(intrinsics.image_width, intrinsics.image_height));
    }

    // we write the default values for aspect ratio, skew, and radial distortion since those cannot
    // be recovered from EXIF
    string filename;
    theia::GetFilenameFromFilepath(input, true, &filename);
    ofs << filename << " " << intrinsics.focal_length.value << " "
        << intrinsics.principal_point[0].value << " " << intrinsics.principal_point[1].value
        << " 1.0 0.0 0.0 0.0\n";
}
