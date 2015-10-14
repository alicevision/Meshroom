#include "Resource.hpp"
#include <QJsonArray>
#include <QVariant>

namespace meshroom
{

Resource::Resource(const QUrl& url)
    : _url(url)
{
}

void Resource::serializeToJSON(QJsonArray* array) const
{
    if(!array)
        return;
    array->append(_url.toLocalFile());
}

} // namespace
