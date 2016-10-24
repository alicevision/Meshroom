#pragma once

#include <QThread>

namespace meshroom
{

class Worker; // forward declaration

class WorkerThread : public QThread
{
    Q_OBJECT

public:
    WorkerThread(QObject*, Worker*);
    ~WorkerThread();

public:
    void run() override;
    void kill();

private:
    Worker* _worker = nullptr;
};

} // namespace
