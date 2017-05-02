#pragma once

#include <QObject>
#include <QFileSystemWatcher>
#include <QProcessEnvironment>
#include <QQuickWindow>
#include <QtQml/QQmlApplicationEngine>
#include <QFileInfo>
#include <QRect>
#include <QDir>
#include <QDebug>
#include <functional>


namespace instantcoding
{

class InstantCoding : public QObject
{
    Q_OBJECT
    typedef std::function<void(const QFileInfo&)> fun_t;

public:
    InstantCoding(QObject* parent, QQmlApplicationEngine&, const QString&);
    ~InstantCoding() = default;

public:
    void start() const;
    void stop() const;
    void addFilesFromDirectory(const QString& path);
    Q_SLOT void fileChanged(const QString& path);

private:
    void traverseDirectory(const QString& path, InstantCoding::fun_t f) const;

private:
    QQmlApplicationEngine& _engine;
    QFileSystemWatcher _watcher;
    QQuickWindow* _window = nullptr;
    QString _file;
};

inline InstantCoding::InstantCoding(QObject* parent, QQmlApplicationEngine& engine, const QString& qmlfile)
    : QObject(parent)
    , _engine(engine)
    , _file(qmlfile)
{

    // traverse the source tree and add all QML files to the fileSystemWatcher
    addFilesFromDirectory(_engine.baseUrl().toLocalFile());

    // callback triggered after a reload
    connect(&_engine, &QQmlApplicationEngine::objectCreated, [&](QObject* root, const QUrl&)
    {
        auto* window = qobject_cast<QQuickWindow*>(root);
        if(!window)
            return;
        if(_window)
        {
            window->setGeometry(_window->geometry());
            _window->deleteLater();
        }
        _window = window;
    });
}

inline void InstantCoding::start() const
{
    connect(&_watcher, &QFileSystemWatcher::fileChanged, this, &InstantCoding::fileChanged);
}

inline void InstantCoding::stop() const
{
    disconnect(&_watcher, &QFileSystemWatcher::fileChanged, this, &InstantCoding::fileChanged);
}

inline void InstantCoding::addFilesFromDirectory(const QString& path)
{
    auto f = [&](const QFileInfo& fileinfo)
    {
        if(fileinfo.completeSuffix() == "qml" || fileinfo.completeSuffix() == "js")
        {
            _watcher.addPath(fileinfo.absoluteFilePath());
            qDebug().noquote() << "QMLIC: Watching QML file" << fileinfo.absoluteFilePath();
        }
    };
    traverseDirectory(path, f);
}

inline Q_SLOT void InstantCoding::fileChanged(const QString& path)
{
    _watcher.removePath(path);
    _engine.clearComponentCache();
    
    // Make sure file is available before doing anything.
    // NOTE: useful to handle editors (Qt Creator) that deletes the source file and creates a new one when saving
    int cpTry = 0;
    QFile file(_engine.baseUrl().toLocalFile() + _file);
    while(!file.exists() && cpTry++ < 15)
        usleep(200);

    _engine.load(_file);
    _watcher.addPath(path);
}

inline void InstantCoding::traverseDirectory(const QString& path, InstantCoding::fun_t f) const
{
    QDir dir(path);
    dir.setFilter(QDir::Dirs | QDir::Files | QDir::NoSymLinks);
    QFileInfoList list = dir.entryInfoList();
    for(int i = 0; i < list.size(); ++i)
    {
        QFileInfo fileInfo = list.at(i);
        if(fileInfo.fileName() == "." || fileInfo.fileName() == "..")
            continue;
        // execute command
        f(fileInfo);
        // traverse children
        if(fileInfo.isDir() && fileInfo.isReadable())
            traverseDirectory(fileInfo.absoluteFilePath(), f);
    }
}

} // namespace
