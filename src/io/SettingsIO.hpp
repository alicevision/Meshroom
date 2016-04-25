#pragma once

#include <QObject>

namespace meshroom
{

class SceneModel; // forward declaration

class SettingsIO
{
public:
    static void clearAll();
    static void clearRecentScenes();
    static void loadRecentScenes(SceneModel* recentModel);
    static void saveRecentScenes(SceneModel* recentModel);
};

} // namespace
