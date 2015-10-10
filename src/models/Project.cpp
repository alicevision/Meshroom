#include "Project.hpp"
#include "io/ProjectsIO.hpp"

namespace mockup
{

Project::Project(const QUrl& url)
    : _url(url)
    , _jobs(new JobModel(this))
    , _proxy(new QSortFilterProxyModel(this))
{
    ProjectsIO::populate(*this);
    _proxy->setSourceModel(_jobs);
    _proxy->setFilterRole(JobModel::NameRole);
}

} // namespace
