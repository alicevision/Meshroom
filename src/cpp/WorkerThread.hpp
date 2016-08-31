#pragma once

#include "Graph.hpp"
#include <QObject>
#include <QThread>
#include <dglib/dg.hpp>

namespace meshroom
{

class WorkerThread : public QThread
{
    Q_OBJECT

public:
    WorkerThread(QObject*, const QString&, Graph::BuildMode, dg::Ptr<dg::Graph>);

public:
    void run() override;
    void kill();

public:
    Q_SIGNAL void nodeStatusChanged(const QString& nodeName, const QString& status);
    Q_SIGNAL void processKilled();

private:
    QString _node;
    Graph::BuildMode _mode;
    dg::Ptr<dg::Graph> _graph;
};

} // namespace
