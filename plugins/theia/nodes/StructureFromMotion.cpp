#include "StructureFromMotion.hpp"
#include <theia/theia.h>
#include <QCommandLineParser>
#include <QDebug>

using namespace std;
using namespace dg;

StructureFromMotion::StructureFromMotion(string nodeName)
    : Node(nodeName)
{
    inputs = {make_ptr<Plug>(Attribute::Type::PATH, "matches", *this),
              make_ptr<Plug>(Attribute::Type::PATH, "exifs", *this),
              make_ptr<Plug>(Attribute::Type::INT, "numThreads", *this),
              make_ptr<Plug>(Attribute::Type::INT, "maxTrackLength", *this),
              make_ptr<Plug>(Attribute::Type::INT, "minNum2ViewsInliers", *this),
              make_ptr<Plug>(Attribute::Type::BOOL, "largestOnly", *this),
              make_ptr<Plug>(Attribute::Type::BOOL, "onlyCalibratedViews", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "reconstructionEstimatorType", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "globalRotationEstimatorType", *this),
              make_ptr<Plug>(Attribute::Type::STRING, "globalPositionEstimatorType", *this)};
    output = make_ptr<Plug>(Attribute::Type::PATH, "reconstruction", *this);
}

vector<Command> StructureFromMotion::prepare(Cache& cache, bool& blocking)
{
    vector<Command> commands;
    auto p1 = plug("matches");
    auto p2 = plug("exifs");
    for(auto& input : cache.slots(p1))
    {
        size_t hash = cache.reserve(*this, {input});
        if(!cache.exists(hash))
        {
            vector<string> options = {
                "-m", "compute",                  // mode
                "-t", type(),                     // type
                "-i", cache.location(input->key), // input
                "-o", cache.location(hash)        // output
            };
            for(auto& exif : cache.slots(p2))
            {
                options.emplace_back("-ex");
                options.emplace_back(cache.location(exif->key));
            }
            Command c(options);
            commands.emplace_back(c);
        }
    }
    return commands;
}

void StructureFromMotion::compute(const vector<string>& arguments) const
{
    qDebug() << "[StructureFromMotion]";

    // command line options
    QCommandLineParser parser;
    parser.setSingleDashWordOptionMode(QCommandLineParser::ParseAsLongOptions);
    parser.addOptions({
        {{"i", "input"}, "match file", "file"},
        {{"ex", "exif"}, "exif file", "file"},
        {{"o", "output"}, "output file", "file"},
    });

    // command line parsing
    parser.parse(QCoreApplication::arguments());
    if(!parser.isSet("input") || !parser.isSet("output"))
        throw logic_error("missing command line value");

    auto toSTDStringVector = [](const QStringList& qlist) -> vector<string>
    {
        vector<string> result;
        for(const auto& qs : qlist)
            result.emplace_back(qs.toStdString());
        return result;
    };

    string input = parser.value("input").toStdString();
    string output = parser.value("output").toStdString();
    vector<string> exifs = toSTDStringVector(parser.values("exif"));
    size_t numthreads = 8;
    bool largestonly = false;
    bool onlycalibratedviews = false;
    int maxtracklength = 10;      // default: 20
    int minnum2viewsinliers = 15; // default: 30
    // string reconstructionestimatortype = "GLOBAL";
    // string globalrotationestimatortype = "ROBUST_L1L2";
    // string reconstructionestimatortype = "LEAST_UNSQUARED_DEVIATION";

    // set up the reconstruction builder
    theia::ReconstructionBuilderOptions options;
    options.num_threads = numthreads;
    options.reconstruct_largest_connected_component = largestonly;
    options.only_calibrated_views = onlycalibratedviews;
    options.max_track_length = maxtracklength;
    options.reconstruction_estimator_options.min_num_two_view_inliers = minnum2viewsinliers;
    options.reconstruction_estimator_options.reconstruction_estimator_type =
        theia::ReconstructionEstimatorType::INCREMENTAL;
    options.reconstruction_estimator_options.global_rotation_estimator_type =
        theia::GlobalRotationEstimatorType::ROBUST_L1L2;
    options.reconstruction_estimator_options.global_position_estimator_type =
        theia::GlobalPositionEstimatorType::NONLINEAR;

    theia::ReconstructionBuilder builder(options);

    // read in match file
    vector<string> images;
    vector<theia::CameraIntrinsicsPrior> intrinsics;
    vector<theia::ImagePairMatch> matches;
    theia::ReadMatchesAndGeometry(input, &images, &intrinsics, &matches);

    // -----------------------
    // read calibration files
    intrinsics.clear();
    unordered_map<string, theia::CameraIntrinsicsPrior> intrinsicsmap;
    for(auto& file : exifs)
        theia::ReadCalibration(file, &intrinsicsmap);

    // prepare intrinsics list
    for(auto& img : images)
    {
        string filename;
        theia::GetFilenameFromFilepath(img, true, &filename);
        auto it = intrinsicsmap.find(filename);
        if(it == intrinsicsmap.end())
            throw logic_error("failed to read exif data");
        intrinsics.emplace_back(it->second);
    }
    // -----------------------

    // add all the views to the builder
    for(int i = 0; i < images.size(); i++)
    {
        if(!builder.AddImageWithCameraIntrinsicsPrior(images[i], intrinsics[i]))
            throw logic_error("failed to configure the reconstruction builder "
                              "(AddImageWithCameraIntrinsicsPrior)");
    }

    // add the matches to the builder
    for(const auto& match : matches)
    {
        if(!builder.AddTwoViewMatch(match.image1, match.image2, match))
            throw logic_error("failed to configure the reconstruction builder (AddTwoViewMatch)");
    }

    // reconstruct
    vector<theia::Reconstruction*> reconstructions;
    if(!builder.BuildReconstruction(&reconstructions))
        throw logic_error("failed to build reconstruction");

    // colorize
    // FIXME do not use this hard-coded path
    theia::ColorizeReconstruction("/tmp/", 4, reconstructions[0]);

    // export
    // FIXME write all reconstruction files
    if(!theia::WriteReconstruction(*reconstructions[0], output))
        throw logic_error("failed to export sfm file");
    qWarning() << "reconstructions: " << reconstructions.size();
}
