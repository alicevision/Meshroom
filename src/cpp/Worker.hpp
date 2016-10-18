#pragma once

#include <QObject>
#include <dglib/dg.hpp>

namespace meshroom
{

class Graph; // forward declaration

class Worker : public QObject
{
    Q_OBJECT

public:
    enum Mode
    {
        PREPARE = 0,
        COMPUTE_LOCAL = 1,
        COMPUTE_TRACTOR = 2,
    };
    Q_ENUMS(Mode)

public:
    Worker(Graph*);

public:
    void compute();
    void killChildProcesses();
    void setNode(const QString& n) { _node = n; }
    void setMode(const Mode& m) { _mode = m; }

public:
    Q_SIGNAL void nodeStatusChanged(const QString& nodeName, const QString& status);

private:
    QString _node;
    Mode _mode = Mode::COMPUTE_LOCAL;
    Graph* _graph = nullptr;
    dg::Runner* _runner = nullptr;
};

} // namespace

// needed in order to use non-local enums as QML signal/slot parameter
// see. https://bugreports.qt.io/browse/QTBUG-20639
Q_DECLARE_METATYPE(meshroom::Worker::Mode)
