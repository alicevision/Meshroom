#include "WorkerThread.hpp"
#include "Worker.hpp"
#include <QDebug>

namespace meshroom
{

WorkerThread::WorkerThread(QObject* parent, Worker* worker)
    : QThread(parent)
    , _worker(worker)
{
}

WorkerThread::~WorkerThread()
{
    delete _worker;
}

void WorkerThread::run()
{
    // start worker
    if(_worker)
        _worker->compute();
}

void WorkerThread::kill()
{
    // stop worker
    if(_worker)
        _worker->killChildProcesses();
    // terminate thread
    terminate();
    wait();
}

} // namespace
