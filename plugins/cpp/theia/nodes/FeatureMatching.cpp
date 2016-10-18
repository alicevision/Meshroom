#include "FeatureMatching.hpp"
#include <theia/theia.h>
#include <QCommandLineParser>
#include <QDebug>

using namespace std;
using namespace dg;

FeatureMatching::FeatureMatching(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::STRING, "features", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "images", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "exifs", *this),
              make_ptr<Plug>(Attribute::Type::INT, "numThreads", *this),
              make_ptr<Plug>(Attribute::Type::INT, "cacheCapacity", *this),
              make_ptr<Plug>(Attribute::Type::FLOAT, "lowesRatio", *this),
              make_ptr<Plug>(Attribute::Type::INT, "minNumFeatureMatches", *this),
              make_ptr<Plug>(Attribute::Type::BOOL, "matchOutOfCore", *this),
              make_ptr<Plug>(Attribute::Type::BOOL, "keepOnlySymmetricMatches", *this),
              make_ptr<Plug>(Attribute::Type::BOOL, "useLowesRatio", *this)};
    output = make_ptr<Plug>(Attribute::Type::STRING, "matches", *this);
}

vector<Command> FeatureMatching::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p1 = plug("features");
    auto p2 = plug("images");
    auto p3 = plug("exifs");

    // one output
    size_t key = cache.key(*this, cache.attributes(p1));
    auto attribute = cache.addAttribute(output, key);

    if(!cache.exists(attribute))
    {
        vector<string> options = {
            "--compute", type(),            // meshroom compute mode
            "--",                           // node options:
            "-o", cache.location(attribute) // output
        };
        for(auto& input : cache.attributes(p1))
        {
            options.emplace_back("-feat");
            options.emplace_back(cache.location(input));
        }
        for(auto& input : cache.attributes(p2))
        {
            options.emplace_back("-img");
            options.emplace_back(cache.location(input));
        }
        for(auto& input : cache.attributes(p3))
        {
            options.emplace_back("-ex");
            options.emplace_back(cache.location(input));
        }
        Command c(options);
        commands.emplace_back(c);
    }
    return commands;
}

void FeatureMatching::compute(const vector<string>& arguments) const
{
    qDebug() << "[FeatureMatching]";

    // command line options
    QCommandLineParser parser;
    parser.setSingleDashWordOptionMode(QCommandLineParser::ParseAsLongOptions);
    parser.addOptions({
        {{"img", "image"}, "image file", "file"},
        {{"feat", "feature"}, "feature file", "file"},
        {{"ex", "exif"}, "exif file", "file"},
        {{"o", "output"}, "output file", "file"},
    });

    // command line parsing
    parser.parse(QCoreApplication::arguments());
    if(!parser.isSet("image") || !parser.isSet("feature") || !parser.isSet("exif") ||
       !parser.isSet("o"))
        throw logic_error("missing command line value");

    auto toSTDStringVector = [](const QStringList& qlist) -> vector<string>
    {
        vector<string> result;
        for(const auto& qs : qlist)
            result.emplace_back(qs.toStdString());
        return result;
    };

    vector<string> images = toSTDStringVector(parser.values("image"));
    vector<string> features = toSTDStringVector(parser.values("feature"));
    vector<string> exifs = toSTDStringVector(parser.values("exif"));
    string output = parser.value("output").toStdString();
    size_t numthreads = 8;
    bool matchoutofcore = false; // false: all in memory
    int cachecapacity = 128;
    bool keeponlysymmetricmatches = true; // default: true
    bool uselowesratio = true;            // default: true
    float lowesratio = 0.8;               // default:0.8
    int minnumfeaturematches = 0;         // default: 30

    // set up the feature matcher
    theia::FeatureMatcherOptions options;
    options.num_threads = numthreads;
    options.match_out_of_core = matchoutofcore;
    options.cache_capacity = cachecapacity;
    options.keep_only_symmetric_matches = keeponlysymmetricmatches;
    options.use_lowes_ratio = uselowesratio;
    options.lowes_ratio = lowesratio;
    options.min_num_feature_matches = minnumfeaturematches;

    // read feature files
    vector<vector<theia::Keypoint>> keypoints;
    vector<vector<Eigen::VectorXf>> descriptors;
    for(size_t i = 0; i < images.size(); ++i)
    {
        vector<theia::Keypoint> keypts;
        vector<Eigen::VectorXf> descs;
        if(!theia::ReadKeypointsAndDescriptors(features[i], &keypts, &descs))
            throw logic_error("failed to read feature data");
        keypoints.emplace_back(keypts);
        descriptors.emplace_back(descs);
    }

    // read calibration files
    unordered_map<string, theia::CameraIntrinsicsPrior> intrinsicsmap;
    for(auto& file : exifs)
        theia::ReadCalibration(file, &intrinsicsmap);

    // prepare intrinsics list
    vector<theia::CameraIntrinsicsPrior> intrinsics;
    for(auto& img : images)
    {
        string filename;
        theia::GetFilenameFromFilepath(img, true, &filename);
        auto it = intrinsicsmap.find(filename);
        if(it == intrinsicsmap.end())
            throw logic_error("failed to read exif data");
        intrinsics.emplace_back(it->second);
    }

    // add all the features to the matcher
    theia::CascadeHashingFeatureMatcher matcher(options);
    // theia::BruteForceFeatureMatcher<theia::L2> matcher(options);
    for(size_t i = 0; i < keypoints.size(); i++)
    {
        string filename;
        theia::GetFilenameFromFilepath(images.at(i), true, &filename);
        matcher.AddImage(filename, keypoints.at(i), descriptors.at(i));
    }

    // match the images
    vector<theia::ImagePairMatch> matches;
    matcher.MatchImages(&matches);

    // export
    if(!theia::WriteMatchesAndGeometry(output, images, intrinsics, matches))
        throw logic_error("failed to export match file");
}
