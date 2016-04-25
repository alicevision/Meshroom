#include "SceneModel.hpp"
#include "io/SettingsIO.hpp"
#include <QQmlEngine>
#include <cassert>

namespace meshroom
{

SceneModel::SceneModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

int SceneModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _scenes.count();
}

QVariant SceneModel::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _scenes.count())
        return QVariant();
    Scene* scene = _scenes[index.row()];
    switch(role)
    {
        case UrlRole:
            return scene->url();
        case NameRole:
            return scene->name();
        case DateRole:
            return scene->date();
        case UserRole:
            return scene->user();
        case ThumbnailRole:
            return scene->thumbnail();
        case DirtyRole:
            return scene->dirty();
        case ModelDataRole:
            return QVariant::fromValue(scene);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> SceneModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[UrlRole] = "url";
    roles[NameRole] = "name";
    roles[DateRole] = "date";
    roles[UserRole] = "user";
    roles[ThumbnailRole] = "thumbnail";
    roles[DirtyRole] = "dirty";
    roles[ModelDataRole] = "modelData";
    return roles;
}

bool SceneModel::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if(index.row() < 0 || index.row() >= _scenes.count())
        return false;
    Scene* scene = _scenes[index.row()];
    switch(role)
    {
        case UrlRole:
            scene->setUrl(value.toUrl());
            break;
        case NameRole:
            scene->setName(value.toString());
            break;
        case DateRole:
            scene->setDate(value.toDateTime());
            break;
        case UserRole:
            scene->setUser(value.toString());
            break;
        case ThumbnailRole:
            scene->setThumbnail(value.toUrl());
            break;
        default:
            return false;
    }
    emit dataChanged(index, index);
    return true;
}

void SceneModel::addScene(Scene* scene)
{
    // do not add the same scene twice
    for(auto s : _scenes)
    {
        if(s->url() == scene->url())
            return;
    }

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(scene, QQmlEngine::CppOwnership);
    scene->setParent(this);

    // insert the new element
    beginInsertRows(QModelIndex(), rowCount(), rowCount());
    _scenes << scene;
    endInsertRows();

    // handle model and contained object synchronization
    QModelIndex id = index(rowCount() - 1, 0);
    auto callback = [id, this]()
    {
        emit dataChanged(id, id);
    };
    connect(scene, &Scene::urlChanged, this, callback);
    connect(scene, &Scene::nameChanged, this, callback);
    connect(scene, &Scene::dateChanged, this, callback);
    connect(scene, &Scene::userChanged, this, callback);
    connect(scene, &Scene::thumbnailChanged, this, callback);
    connect(scene, &Scene::dirtyChanged, this, callback);

    emit countChanged(rowCount());
    SettingsIO::saveRecentScenes(this);
}

void SceneModel::addScene(const QUrl& url)
{
    Scene* scene = new Scene(url);
    addScene(scene);
}

void SceneModel::removeScene(Scene* scene)
{
    // ensure that we have at least one scene
    if(rowCount() == 1)
    {
        Scene* newScene = new Scene(scene->url());
        addScene(newScene);
    }
    // find and remove the scene
    int id = _scenes.indexOf(scene);
    if(id < 0)
        return;
    beginRemoveRows(QModelIndex(), id, id);
    _scenes.removeAt(id);
    delete scene;
    endRemoveRows();

    emit countChanged(rowCount());
    SettingsIO::saveRecentScenes(this);
}

QVariantMap SceneModel::get(int row) const
{
    QHash<int, QByteArray> names = roleNames();
    QHashIterator<int, QByteArray> i(names);
    QVariantMap result;
    while(i.hasNext())
    {
        i.next();
        QModelIndex idx = index(row, 0);
        QVariant data = idx.data(i.key());
        result[i.value()] = data;
    }
    return result;
}

} // namespace
