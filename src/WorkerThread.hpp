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
    Q_SIGNAL void nodeVisitStarted(const QString& s);
    Q_SIGNAL void nodeVisitCompleted(const QString& s);
    Q_SIGNAL void nodeComputeStarted(const QString& s);
    Q_SIGNAL void nodeComputeCompleted(const QString& s);
    Q_SIGNAL void nodeComputeFailed(const QString& s);

private:
    QString _nodeName;
    Graph::BuildMode _mode;
    dg::Ptr<dg::Graph> _graph;
};

} // namespace
