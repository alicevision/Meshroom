#pragma once

#include <QObject>
#include <QSettings>

namespace meshroom
{

class Settings : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QVariantList recentFiles READ recentFiles NOTIFY recentFilesChanged)

public:
    Settings() = default;
    Q_INVOKABLE QVariantList recentFiles() const;
    Q_INVOKABLE void addRecentFile(const QUrl&);
    Q_INVOKABLE void clearRecentFiles();

public:
    Q_SIGNAL void recentFilesChanged();

private:
    QSettings _settings;
};

inline void Settings::addRecentFile(const QUrl& url)
{
    auto recent = recentFiles();
    if(recent.contains(QVariant(url)))
        return;
    recent.append(url);
    _settings.setValue("scene/recent", recent);
    Q_EMIT recentFilesChanged();
}

inline void Settings::clearRecentFiles()
{
    QVariantList empty;
    _settings.setValue("scene/recent", empty);
    Q_EMIT recentFilesChanged();
}

inline QVariantList Settings::recentFiles() const
{
    return _settings.value("scene/recent").toList();
}

} // namespace
