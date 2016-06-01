#include "PlyExport.hpp"
#include <theia/theia.h>
#include <QCommandLineParser>
#include <QDebug>

using namespace std;
using namespace dg;

PlyExport::PlyExport(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::PATH, "reconstructions", *this)};
    output = make_ptr<Plug>(Attribute::Type::PATH, "output", *this);
}

vector<Command> PlyExport::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p = plug("reconstructions");
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

void PlyExport::compute(const vector<string>& arguments) const
{
    qDebug() << "[PlyExport]";

    // command line options
    QCommandLineParser parser;
    parser.setSingleDashWordOptionMode(QCommandLineParser::ParseAsLongOptions);
    parser.addOptions({
        {{"i", "input"}, "image file", "file"},
        {{"o", "output"}, "exif file", "file"},
    });

    // command line parsing
    parser.parse(QCoreApplication::arguments());
    if(!parser.isSet("input") || !parser.isSet("output"))
    {
        qCritical() << "missing command line value";
        return;
    }
    string input = parser.value("input").toStdString();
    string output = parser.value("output").toStdString();

    // read all reconstruction files
    theia::Reconstruction reconstruction;
    if(!theia::ReadReconstruction(input, &reconstruction))
    {
        qCritical() << " | ERROR (reading reconstruction)";
        return;
    }

    // write as PLY files
    int minnumobservationsperpoint = 0;
    if(!theia::WritePlyFile(output, reconstruction, minnumobservationsperpoint))
    {
        qCritical() << " | ERROR (writing ply file)";
        return;
    }
}
