#pragma once

#include <QObject>

namespace mockup
{

class ProjectModel; // forward declaration

class ProjectsIO
{
public:
    static ProjectModel* create(QObject* parent);
    static ProjectModel* load(QObject* parent, const QUrl& url);
};

} // namespace
