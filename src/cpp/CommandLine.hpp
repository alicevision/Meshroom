#pragma once

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
        RUN_LOCAL,
        RUN_TRACTOR,
        QUIT_FAILURE,
        QUIT_SUCCESS
    };

public:
    CommandLine();
    CommandLine(const CommandLine& obj) = delete;
    CommandLine& operator=(CommandLine const&) = delete;
    ~CommandLine() = default;

public:
    void parse(int& argc, char** argv);
    const MODE& mode() const { return _mode; }
    QString nodeType() const { return _parser.value("type"); }
    QString nodeName() const { return _parser.value("name"); }
    QUrl sceneURL() const { return QUrl::fromLocalFile(_parser.value("scene")); }

private:
    QCommandLineParser _parser;
    MODE _mode = OPEN_GUI;
};

} // namespaces
