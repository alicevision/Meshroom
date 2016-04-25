#pragma once

#include <QObject>
#include <QFileSystemWatcher>
#include <QtQml/QQmlApplicationEngine>
#include <functional>

class QFileInfo; // forward reference

namespace instantcoding
{

class InstantCoding : public QObject
{
    Q_OBJECT
    typedef std::function<void(const QFileInfo&)> fun_t;

public:
    InstantCoding(QQmlApplicationEngine& engine);
    ~InstantCoding() = default;

public:
    void watch(const QString& path);

public slots:
    void fileChanged(const QString& path);

private:
    void traverseDirectory(const QString& path, InstantCoding::fun_t f);

private:
    QQmlApplicationEngine& _engine;
    QFileSystemWatcher _watcher;
};

} // namespace
