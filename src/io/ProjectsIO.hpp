#pragma once

#include <QObject>

namespace mockup
{

class ProjectModel; // forward declaration

class ProjectsIO
{
public:
    static ProjectModel* load(QObject* parent, const QUrl& url);
};

} // namespace
