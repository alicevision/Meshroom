#pragma once

#include <QObject>

namespace mockup
{

class Application; // forward declaration

class SettingsIO : public QObject
{
    Q_OBJECT

public:
    SettingsIO(Application& app);
    ~SettingsIO() = default;

public:
    void load() const;
    void clear() const;
    void clearRecentProjects() const;
    QVariantList recentProjects() const;
    void addToRecentProjects(const QUrl& url) const;
    void removeFromRecentProjects(const QUrl& url) const;

private:
    Application& _application;
};

} // namespace
