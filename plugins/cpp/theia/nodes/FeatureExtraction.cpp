#include "FeatureExtraction.hpp"
#include <theia/theia.h>
#include <QCommandLineParser>
#include <QDebug>

using namespace std;
using namespace dg;

FeatureExtraction::FeatureExtraction(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "images", *this),
              make_ptr<Plug>(Attribute::Type::INT, "numThreads", *this),
              make_ptr<Plug>(Attribute::Type::INT, "maxNumFeatures", *this),
              make_ptr<Plug>(Attribute::Type::INT, "numOctave", *this),
              make_ptr<Plug>(Attribute::Type::INT, "numLevels", *this),
              make_ptr<Plug>(Attribute::Type::INT, "firstOctave", *this),
              make_ptr<Plug>(Attribute::Type::FLOAT, "edgeThreshold", *this),
              make_ptr<Plug>(Attribute::Type::FLOAT, "peakThreshold", *this),
              make_ptr<Plug>(Attribute::Type::BOOL, "rootSift", *this),
              make_ptr<Plug>(Attribute::Type::BOOL, "uprightSift", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "features", *this);
}

vector<Command> FeatureExtraction::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p = plug("images");
    for(auto& input : cache.attributes(p))
    {
        size_t key = cache.key(*this, {input});
        auto attribute = cache.addAttribute(output, key);
        if(!cache.exists(attribute))
        {
            Command c({
                "-m", "compute",                // mode
                "-t", type(),                   // type
                "-i", cache.location(input),    // input
                "-o", cache.location(attribute) // output
            });
            commands.emplace_back(c);
        }
    }
    return commands;
}

void FeatureExtraction::compute(const vector<string>& arguments) const
{
    qDebug() << "[FeatureExtraction]";

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
    size_t numthreads = 8;
    size_t maxnumfeatures = 16384;
    size_t numoctaves = -1;
    size_t numlevels = 3;
    size_t firstoctave = 0;
    float edgethreshold = 5.0f;
    float peakthreshold = 0.5f;
    bool rootsift = true;
    bool uprightsift = true;

    // set up the feature extractor
    theia::FeatureExtractor::Options options;
    options.descriptor_extractor_type = theia::DescriptorExtractorType::SIFT;
    options.num_threads = numthreads;
    options.max_num_features = maxnumfeatures;
    options.feature_density = theia::FeatureDensity::DENSE;
    // options.sift_parameters.num_octaves = numoctaves;
    // options.sift_parameters.num_levels = numlevels;
    // options.sift_parameters.first_octave = firstoctave;
    // options.sift_parameters.edge_threshold = edgethreshold;
    // options.sift_parameters.peak_threshold = peakthreshold;
    // options.sift_parameters.root_sift = rootsift;
    // options.sift_parameters.upright_sift = uprightsift;

    // extract features
    theia::FeatureExtractor extractor(options);
    vector<vector<theia::Keypoint>> keypoints;
    vector<vector<Eigen::VectorXf>> descriptors;
    if(!extractor.Extract({input}, &keypoints, &descriptors))
        throw logic_error("failed to extract feature descriptor");

    // export
    if(!theia::WriteKeypointsAndDescriptors(output, keypoints[0], descriptors[0]))
        throw logic_error("failed to export feature file");
}
