#include "Project.hpp"
#include "io/ProjectsIO.hpp"

namespace mockup
{

Project::Project(const QUrl& url)
    : _url(url)
    , _jobs(new JobModel(this))
{
    ProjectsIO::populate(*this);
}

} // namespace
