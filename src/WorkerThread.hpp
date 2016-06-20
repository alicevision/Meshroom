#pragma once

#include "models/Graph.hpp"
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

public:
    Q_SIGNAL void nodeStatusChanged(const QString& nodeName, const QString& status);

private:
    QString _nodeName;
    Graph::BuildMode _mode;
    dg::Ptr<dg::Graph> _graph;
};

} // namespace
