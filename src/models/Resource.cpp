#include "Resource.hpp"
#include <QFileInfo>
#include <QJsonArray>
#include <QDebug>

namespace meshroom
{

Resource::Resource(const QUrl& url)
    : _url(url)
{
    QFileInfo fi(url.toLocalFile());
    if(!fi.exists())
        _exists = false;
}

Resource::Resource(const Resource& obj)
    : _url(obj.url())
    , _exists(obj.exists())
{
}

void Resource::serializeToJSON(QJsonArray* array) const
{
    if(!array)
        return;
    array->append(_url.toLocalFile());
}

} // namespace
