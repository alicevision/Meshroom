#include "SettingsIO.hpp"
#include <QSettings>
#include <QUrl>
#include <QDir>
#include <cstdlib> // std::getenv

namespace meshroom
{

void SettingsIO::clearAll()
{
    QSettings settings;
    settings.clear();
}

void SettingsIO::clearRecentScenes()
{
    QSettings settings;
    QVariantList empty;
    settings.setValue("scene/recent", empty);
}

// void SettingsIO::loadRecentScenes(SceneModel* sceneModel)
// {
//     QSettings settings;
//     QVariantList recents = settings.value("scene/recent").toList();
//     QVariantList::iterator it = recents.begin();
//     QList<QObject*> scenes;
//     while(it != recents.end())
//     {
//         QUrl url(it->toUrl());
//         sceneModel->addScene(url);
//         ++it;
//     }
// }
//
// void SettingsIO::saveRecentScenes(SceneModel* sceneModel)
// {
//     // clear recent project list
//     SettingsIO::clearRecentScenes();
//     // rebuild it by iterating over all loaded scenes
//     QSettings settings;
//     QVariantList recents;
//     for(size_t i = 0; i < sceneModel->rowCount(); ++i)
//     {
//         QModelIndex id = sceneModel->index(i, 0);
//         Scene* j = sceneModel->data(id, SceneModel::ModelDataRole).value<Scene*>();
//         if(!j || !j->url().isValid())
//             continue;
//         recents.append(j->url());
//     }
//     settings.setValue("scene/recent", recents);
// }

} // namespace
