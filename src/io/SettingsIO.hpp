#pragma once

#include <QObject>

namespace mockup
{

class ProjectModel; // forward declaration
class ResourceModel; // forward declaration

class SettingsIO
{
public:
    static void clearAll();
    static void clearRecentProjects();
    static void loadRecentProjects(ProjectModel* recentModel);
    static void saveRecentProjects(ProjectModel* recentModel);
    static void loadFeaturedProjects(ResourceModel* featuredModel);
};

} // namespace
