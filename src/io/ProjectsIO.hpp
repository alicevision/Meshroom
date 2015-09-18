#pragma once

#include <QObject>

namespace mockup
{

class Project; // forward declaration

class ProjectsIO
{
public:
    static void populate(Project& project);
};

} // namespace
