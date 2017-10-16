from collections import defaultdict
import psutil
import time
import threading


def bytes2human(n):
    """
    >>> bytes2human(10000)
    '9.8 K/s'
    >>> bytes2human(100001221)
    '95.4 M/s'
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.2f %s' % (value, s)
    return '%.2f B' % (n)


class ComputerStatistics:
    def __init__(self):
        # TODO: init
        self.nbCores = 0
        self.cpuFreq = 0
        self.ramAvailable = 0  # GB
        self.vramAvailable = 0  # GB
        self.swapAvailable = 0

        self.curves = defaultdict(list)

    def _addKV(self, k, v):
        if isinstance(v, tuple):
            for ki, vi in v._asdict().items():
                self._addKV(k + '.' + ki, vi)
        elif isinstance(v, list):
            for ki, vi in enumerate(v):
                self._addKV(k + '.' + str(ki), vi)
        else:
            self.curves[k].append(v)

    def update(self):
        self._addKV('cpuUsage', psutil.cpu_percent(percpu=True)) # interval=None => non-blocking (percentage since last call)
        self._addKV('ramUsage', psutil.virtual_memory().percent)
        self._addKV('swapUsage', psutil.swap_memory().percent)
        self._addKV('vramUsage', 0)
        self._addKV('ioCounters', psutil.disk_io_counters())

    def toDict(self):
        return self.__dict__

    def fromDict(self, d):
        for k, v in d.items():
            setattr(self, k, v)

class ProcStatistics:
    staticKeys = [
        'pid',
        'nice',
        'cpu_times',
        'create_time',
        'environ',
        'ionice',
        # 'gids',
        # 'uids',
        'cpu_num',
        'cwd',
        'cmdline',
        'cpu_affinity',
        # 'ppid',
        # 'name',
        # 'exe',
        # 'terminal',
        'username',
        ]
    dynamicKeys = [
        # 'memory_full_info',
        # 'connections',
        'cpu_percent',
        # 'open_files',
        'memory_info',
        'memory_percent',
        'threads',
        'num_threads',
        # 'memory_maps',
        'status',
        'num_fds', # The number of file descriptors currently opened by this process (non cumulative)
        'io_counters',
        'num_ctx_switches',
        ]

    def __init__(self):
        self.iterIndex = 0
        self.lastIterIndexWithFiles = -1
        self.duration = 0  # computation time set at the end of the execution
        self.curves = defaultdict(list)
        self.openFiles = {}

    def _addKV(self, k, v):
        if isinstance(v, tuple):
            for ki, vi in v._asdict().items():
                self._addKV(k + '.' + ki, vi)
        elif isinstance(v, list):
            for ki, vi in enumerate(v):
                self._addKV(k + '.' + str(ki), vi)
        else:
            self.curves[k].append(v)

    def update(self, proc):
        '''
        proc: psutil.Process object
        '''
        data = proc.as_dict(self.dynamicKeys)
        for k, v in data.items():
            self._addKV(k, v)

        files = [f.path for f in proc.open_files()]
        if self.lastIterIndexWithFiles != -1:
            if set(files) != set(self.openFiles[self.lastIterIndexWithFiles]):
                self.openFiles[self.iterIndex] = files
                self.lastIterIndexWithFiles = self.iterIndex
        elif files:
            self.openFiles[self.iterIndex] = files
            self.lastIterIndexWithFiles = self.iterIndex
        self.iterIndex += 1

    def toDict(self):
        return {
            'duration': self.duration,
            'curves': self.curves,
            'openFiles': self.openFiles,
        }

    def fromDict(self, d):
        self.duration = d.get('duration', 0)
        self.curves = d.get('curves', defaultdict(list))
        self.openFiles = d.get('openFiles', {})


class Statistics:
    """
    """
    fileVersion = 1.0

    def __init__(self):
        self.computer = ComputerStatistics()
        self.process = ProcStatistics()
        self.times = []

    def update(self, proc):
        '''
        proc: psutil.Process object
        '''
        if proc is None or not proc.is_running():
            return False
        self.times.append(time.time())
        self.computer.update()
        self.process.update(proc)
        return True

    def toDict(self):
        return {
            'fileVersion': self.fileVersion,
            'computer': self.computer.toDict(),
            'process': self.process.toDict(),
            'times': self.times,
            }

    def fromDict(self, d):
        version = d.get('fileVersion', 1.0)
        if version != self.fileVersion:
            logging.info('Cannot load statistics, version was {} and we only support {}.'.format(version, fileVersion))
            self.computer = {}
            self.process = {}
            self.times = []
            return
        self.computer.fromDict(d.get('computer', {}))
        self.process.fromDict(d.get('process', {}))
        self.times = d.get('times', [])


bytesPerGiga = 1024. * 1024. * 1024.


class StatisticsThread(threading.Thread):
    def __init__(self, node):
        threading.Thread.__init__(self)
        self.node = node
        self.proc = None
        self.statistics = self.node.statistics
        self._stopFlag = threading.Event()

    def updateStats(self):
        self.lastTime = time.time()
        if self.statistics.update(self.proc):
            self.node.saveStatistics()

    def run(self):
        while True:
            self.updateStats()
            if self._stopFlag.wait(60):
                # stopFlag has been set
                # update stats one last time and exit main loop
                self.updateStats()
                return

    def stopRequest(self):
        """ Request the thread to exit as soon as possible. """
        self._stopFlag.set()
