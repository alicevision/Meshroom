#pragma once

#include <QObject>

namespace mockup
{

class ApplicationModel; // forward declaration

class SettingsIO
{
public:
    static void clearAll();
    static void clearRecentProjects();
    static void loadRecentProjects(ApplicationModel& applicationModel);
    static void saveRecentProjects(ApplicationModel& applicationModel);
};

} // namespace
