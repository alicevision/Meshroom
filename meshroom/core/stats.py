from collections import defaultdict
import subprocess
import logging
import psutil
import time
import threading
import platform
import os

import xml.etree.ElementTree as ET


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
        self.nbCores = 0
        self.cpuFreq = 0
        self.ramTotal = 0
        self.ramAvailable = 0  # GB
        self.vramAvailable = 0  # GB
        self.swapAvailable = 0
        self.gpuMemoryTotal = 0
        self.gpuName = ''
        self.curves = defaultdict(list)
        self.nvidia_smi = None
        self._isInit = False

    def initOnFirstTime(self):
        if self._isInit:
            return
        self._isInit = True

        self.cpuFreq = psutil.cpu_freq().max
        self.ramTotal = psutil.virtual_memory().total / (1024*1024*1024)

        if platform.system() == "Windows":
            from distutils import spawn
            # If the platform is Windows and nvidia-smi
            self.nvidia_smi = spawn.find_executable('nvidia-smi')
            if self.nvidia_smi is None:
                # Could not be found from the environment path,
                # try to find it from system drive with default installation path
                default_nvidia_smi = "%s\\Program Files\\NVIDIA Corporation\\NVSMI\\nvidia-smi.exe" % os.environ['systemdrive']
                if os.path.isfile(default_nvidia_smi):
                    self.nvidia_smi = default_nvidia_smi
        else:
            self.nvidia_smi = "nvidia-smi"

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
        try:
            self.initOnFirstTime()
            # Interval=None => non-blocking (percentage since last call)
            self._addKV('cpuUsage', psutil.cpu_percent(percpu=True))
            self._addKV('ramUsage', psutil.virtual_memory().percent)
            self._addKV('swapUsage', psutil.swap_memory().percent)
            self._addKV('vramUsage', 0)
            self._addKV('ioCounters', psutil.disk_io_counters())
            self.updateGpu()
        except Exception as e:
            logging.debug('Failed to get statistics: "{}".'.format(str(e)))

    def updateGpu(self):
        if not self.nvidia_smi:
            return
        try:
            p = subprocess.Popen([self.nvidia_smi, "-q", "-x"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            xmlGpu, stdError = p.communicate(timeout=10)  # 10 seconds

            smiTree = ET.fromstring(xmlGpu)
            gpuTree = smiTree.find('gpu')

            try:
                self.gpuName = gpuTree.find('product_name').text
            except Exception as e:
                logging.debug('Failed to get gpuName: "{}".'.format(str(e)))
                pass
            try:
                gpuMemoryUsed = gpuTree.find('fb_memory_usage').find('used').text.split(" ")[0]
                self._addKV('gpuMemoryUsed', gpuMemoryUsed)
            except Exception as e:
                logging.debug('Failed to get gpuMemoryUsed: "{}".'.format(str(e)))
                pass
            try:
                self.gpuMemoryTotal = gpuTree.find('fb_memory_usage').find('total').text.split(" ")[0]
            except Exception as e:
                logging.debug('Failed to get gpuMemoryTotal: "{}".'.format(str(e)))
                pass
            try:
                gpuUsed = gpuTree.find('utilization').find('gpu_util').text.split(" ")[0]
                self._addKV('gpuUsed', gpuUsed)
            except Exception as e:
                logging.debug('Failed to get gpuUsed: "{}".'.format(str(e)))
                pass
            try:
                gpuTemperature = gpuTree.find('temperature').find('gpu_temp').text.split(" ")[0]
                self._addKV('gpuTemperature', gpuTemperature)
            except Exception as e:
                logging.debug('Failed to get gpuTemperature: "{}".'.format(str(e)))
                pass
        except subprocess.TimeoutExpired as e:
            logging.debug('Timeout when retrieving information from nvidia_smi: "{}".'.format(str(e)))
            p.kill()
            outs, errs = p.communicate()
            return
        except Exception as e:
            logging.debug('Failed to get information from nvidia_smi: "{}".'.format(str(e)))
            return

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
        # 'num_fds', # The number of file descriptors currently opened by this process (non cumulative) - N/A on Windows
        # 'io_counters', # The number and bytes read/write by the process - N/A on some platforms
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

        # Note: Do not collect stats about open files for now,
        #        as there is bug in psutil-5.7.2 on Windows which crashes the application.
        #        https://github.com/giampaolo/psutil/issues/1763
        #
        # files = [f.path for f in proc.open_files()]
        # if self.lastIterIndexWithFiles != -1:
        #     if set(files) != set(self.openFiles[self.lastIterIndexWithFiles]):
        #         self.openFiles[self.iterIndex] = files
        #         self.lastIterIndexWithFiles = self.iterIndex
        # elif files:
        #     self.openFiles[self.iterIndex] = files
        #     self.lastIterIndexWithFiles = self.iterIndex
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
    fileVersion = 2.0

    def __init__(self):
        self.computer = ComputerStatistics()
        self.process = ProcStatistics()
        self.times = []
        self.interval = 10  # refresh interval in seconds

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
            'interval': self.interval
            }

    def fromDict(self, d):
        version = d.get('fileVersion', 0.0)
        if version != self.fileVersion:
            logging.debug('Statistics: file version was {} and the current version is {}.'.format(version, self.fileVersion))
        self.computer = ComputerStatistics()
        self.process = ProcStatistics()
        self.times = []
        try:
            self.computer.fromDict(d.get('computer', {}))
        except Exception as e:
            logging.debug('Failed while loading statistics: computer: "{}".'.format(str(e)))
        try:
            self.process.fromDict(d.get('process', {}))
        except Exception as e:
            logging.debug('Failed while loading statistics: process: "{}".'.format(str(e)))
        try:
            self.times = d.get('times', [])
        except Exception as e:
            logging.debug('Failed while loading statistics: times: "{}".'.format(str(e)))


bytesPerGiga = 1024. * 1024. * 1024.


class StatisticsThread(threading.Thread):
    def __init__(self, chunk):
        threading.Thread.__init__(self)
        self.chunk = chunk
        self.proc = psutil.Process()  # by default current process pid
        self.statistics = chunk.statistics
        self._stopFlag = threading.Event()

    def updateStats(self):
        self.lastTime = time.time()
        if self.chunk.statistics.update(self.proc):
            self.chunk.saveStatistics()

    def run(self):
        try:
            while True:
                self.updateStats()
                if self._stopFlag.wait(self.statistics.interval):
                    # stopFlag has been set
                    # update stats one last time and exit main loop
                    if self.proc.is_running():
                        self.updateStats()
                    return
        except (KeyboardInterrupt, SystemError, GeneratorExit, psutil.NoSuchProcess):
            pass

    def stopRequest(self):
        """ Request the thread to exit as soon as possible. """
        self._stopFlag.set()
