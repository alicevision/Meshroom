#include "PlyExport.hpp"
#include <theia/theia.h>
#include <QCommandLineParser>
#include <QDebug>

using namespace std;
using namespace dg;

PlyExport::PlyExport(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "reconstructions", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "output", *this);
}

vector<Command> PlyExport::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p = plug("reconstructions");
    for(auto& input : cache.attributes(p))
    {
        size_t key = cache.key(*this, {input});
        auto attribute = cache.addAttribute(output, key);
        if(!cache.exists(attribute))
        {
            Command c(
                {
                    "--compute", type(),            // meshroom compute mode
                    "--",                           // node options:
                    "-i", cache.location(input),    // input
                    "-o", cache.location(attribute) // output
                },
                environment);
            commands.emplace_back(c);
        }
    }
    return commands;
}

void PlyExport::compute(const vector<string>& arguments) const
{
    qDebug() << "[PlyExport]";

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

    // read all reconstruction files
    theia::Reconstruction reconstruction;
    if(!theia::ReadReconstruction(input, &reconstruction))
        throw logic_error("failed to read the reconstruction file");

    // write as PLY files
    int minnumobservationsperpoint = 0;
    if(!theia::WritePlyFile(output, reconstruction, minnumobservationsperpoint))
        throw logic_error("failed to export .ply file");
}
