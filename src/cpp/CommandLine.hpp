#pragma once

#include "Worker.hpp"
#include <QCommandLineParser>
#include <QUrl>

namespace meshroom
{

class CommandLine
{
public:
    enum MODE
    {
        OPEN_GUI = 0,
        COMPUTE_NODE,
        COMPUTE_GRAPH
    };

public:
    CommandLine();
    CommandLine(const CommandLine& obj) = delete;
    CommandLine& operator=(CommandLine const&) = delete;
    ~CommandLine() = default;

public:
    void build(int& argc, char** argv);
    void parse(const QCoreApplication& qapp);
    const MODE& mode() const { return _mode; }
    QString nodeType() const { return _parser.value("compute"); }
    QString nodeName() const { return _parser.value("node"); }
    QUrl sceneURL() const;
    Worker::Mode buildMode() const;
    std::vector<std::string> positionalArguments() const;

private:
    QCommandLineParser _parser;
    MODE _mode = OPEN_GUI;
};

} // namespaces
