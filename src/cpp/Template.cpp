#include "Template.hpp"
#include <QFileInfo>
#include <QDebug>

namespace meshroom
{

Template::Template(QObject* parent, const QUrl& url)
    : QObject(parent)
    , _url(url)
    , _name(QFileInfo(url.toLocalFile()).baseName())
{
}

} // namespace
