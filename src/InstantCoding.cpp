#include "InstantCoding.hpp"
#include <QQmlContext>
#include <QDir>
#include <QFileInfo>
#include <iostream>

namespace mockup
{

InstantCoding::InstantCoding(QQmlApplicationEngine& engine)
    : _engine(engine)
{
    QObject::connect(&_watcher, SIGNAL(fileChanged(QString)), this, SLOT(fileChanged(QString)));
}

void InstantCoding::watch(const QString& path)
{
    fun_t f = [&](const QFileInfo& fileinfo)
    {
        if(fileinfo.completeSuffix() == "qml")
        {
            _watcher.addPath(fileinfo.absoluteFilePath());
            std::cout << "Watching QML file: " << fileinfo.absoluteFilePath().toStdString() << std::endl;
        }
    };
    traverseDirectory(path, f);
}

void InstantCoding::fileChanged(const QString& path)
{
    std::cout << "QML file changed: " << path.toStdString() << std::endl;
    QList<QObject*> rootObjects = _engine.rootObjects();
    foreach(QObject* obj, rootObjects)
    {
        QObject *loader = obj->findChild<QObject*>("instanCodingLoader");
        if(loader)
        {
            /*
            // clear QRC scheme from object's context
            QQmlContext *context = _engine.contextForObject(loader);
            context->setBaseUrl(QUrl::fromLocalFile(""));
            */
            QVariant source = loader->property("source");
            QString sourceStr = source.toString().remove("qrc:/");
            loader->setProperty("source", "");
            _engine.clearComponentCache();
            loader->setProperty("source", sourceStr);
        }
    }
}

// private
void InstantCoding::traverseDirectory(const QString& path, InstantCoding::fun_t f)
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
