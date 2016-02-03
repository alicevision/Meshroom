#include "Resource.hpp"
#include <QJsonArray>

namespace meshroom
{

Resource::Resource(const QUrl& url)
    : _url(url)
{
}

Resource::Resource(const Resource& obj)
    : _url(obj.url())
{
}

void Resource::serializeToJSON(QJsonArray* array) const
{
    if(!array)
        return;
    array->append(_url.toLocalFile());
}

} // namespace
