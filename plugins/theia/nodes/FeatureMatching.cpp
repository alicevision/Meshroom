#include "FeatureMatching.hpp"
#include <theia/theia.h>
#include <QCommandLineParser>
#include <QDebug>

using namespace std;
using namespace dg;

FeatureMatching::FeatureMatching(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::PATH, "features", *this),
              make_ptr<Plug>(Attribute::Type::PATH, "images", *this),
              make_ptr<Plug>(Attribute::Type::PATH, "exifs", *this)};
    output = make_ptr<Plug>(Attribute::Type::PATH, "matches", *this);
}

vector<Command> FeatureMatching::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p1 = plug("features");
    auto p2 = plug("images");
    auto p3 = plug("exifs");

    // one output
    size_t hash = cache.reserve(*this, cache.slots(p1));

    if(!cache.exists(hash))
    {
        vector<string> options = {
            "-m", "compute",           // mode
            "-t", type(),              // type
            "-o", cache.location(hash) // output
        };
        for(auto& input : cache.slots(p1))
        {
            options.emplace_back("-feat");
            options.emplace_back(cache.location(input->key));
        }
        for(auto& input : cache.slots(p2))
        {
            options.emplace_back("-img");
            options.emplace_back(cache.location(input->key));
        }
        for(auto& input : cache.slots(p3))
        {
            options.emplace_back("-ex");
            options.emplace_back(cache.location(input->key));
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
    if(!parser.isSet("image") || !parser.isSet("feature") || !parser.isSet("exif") || !parser.isSet("o"))
    {
        qCritical() << "missing command line value";
        return;
    }

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
    bool keeponlysymmetricmatches = true;
    bool uselowesratio = true;
    float lowesratio = 0.8;
    int minnumfeaturematches = 30;

    // // parse node arguments
    // for(int i = 0; i < arguments.size(); ++i)
    // {
    //     const string& option = arguments[i];
    //     if(matches(option, "--images", "-img"))
    //         getArgs(arguments, ++i, images);
    //     else if(matches(option, "--features", "-feat"))
    //         getArgs(arguments, ++i, features);
    //     else if(matches(option, "--exifs", "-ex"))
    //         getArgs(arguments, ++i, exifs);
    //     else if(matches(option, "--output", "-o"))
    //         getArgs(arguments, ++i, output);
    //     else if(matches(option, "--threads", "-th"))
    //         getArgs(arguments, ++i, numthreads);
    //     else if(matches(option, "--outofcore", "-ooc"))
    //         getArgs(arguments, ++i, matchoutofcore);
    //     else if(matches(option, "--cachecapacity", "-cc"))
    //         getArgs(arguments, ++i, cachecapacity);
    //     else if(matches(option, "--keeponlysymetric", "-kos"))
    //         getArgs(arguments, ++i, keeponlysymmetricmatches);
    //     else if(matches(option, "--uselowesratio", "-ulr"))
    //         getArgs(arguments, ++i, uselowesratio);
    //     else if(matches(option, "--lowesratio", "-lr"))
    //         getArgs(arguments, ++i, lowesratio);
    //     else if(matches(option, "--minfeatures", "-mf"))
    //         getArgs(arguments, ++i, minnumfeaturematches);
    // }
    // if(features.empty() || images.empty() || output.empty())
    //     throw logic_error("missing command line value");

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
        {
            qCritical() << " | ERROR (reading features)";
            return;
        }
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
        {
            qCritical() << " | ERROR (intrinsics not found)";
            return;
        }
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
    {
        qCritical() << " | ERROR (export)";
        return;
    }
}
