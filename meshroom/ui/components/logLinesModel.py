from PySide6.QtCore import QAbstractListModel, Qt, QModelIndex, Slot, QObject, Property

import re
from enum import IntEnum


class LogLevel(IntEnum):
    """
    Enum for log levels.
    
    These values can be used in QML for filtering, styling, or conditional logic.
    """
    UNKNOWN = 0
    TRACE = 1
    DEBUG = 2
    INFO = 3
    WARNING = 4
    ERROR = 5
    CRITICAL = 6
    FATAL = 7


class LogLevelEnum(QObject):
    """
    Wrapper class to expose LogLevel enum to QML.
    
    Usage in QML:
        import DataObjects 1.0
        
        if (level === LogLevelEnum.ERROR) {
            // Handle error
        }
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)

    @Property(int, constant=True)
    def UNKNOWN(self):
        return int(LogLevel.UNKNOWN)
    
    @Property(int, constant=True)
    def TRACE(self):
        return int(LogLevel.TRACE)
    
    @Property(int, constant=True)
    def DEBUG(self):
        return int(LogLevel.DEBUG)
    
    @Property(int, constant=True)
    def INFO(self):
        return int(LogLevel.INFO)
    
    @Property(int, constant=True)
    def WARNING(self):
        return int(LogLevel.WARNING)
    
    @Property(int, constant=True)
    def ERROR(self):
        return int(LogLevel.ERROR)
    
    @Property(int, constant=True)
    def CRITICAL(self):
        return int(LogLevel.CRITICAL)
    
    @Property(int, constant=True)
    def FATAL(self):
        return int(LogLevel.FATAL)

class LogLinesModel(QAbstractListModel):
    """
    Model for log lines with duration tracking.
    
    This Qt model parses log text and extracts metadata including timestamps,
    log levels, and calculates the duration (in seconds) between consecutive
    timestamped log entries.
    
    Expected log format:
        [HH:MM:SS][LEVEL][optional:numbers] message text
        Example: [12:34:56][INFO][1:23] Application started
    
    Each item in the model contains:
        - line: The message text (without metadata)
        - time: The timestamp string (HH:MM:SS)
        - level: The log level as an enum (LogLevel)
        - duration: Seconds elapsed since the previous timestamped line (-1 if not applicable)
    
    Attributes:
        LineRole: Custom role for accessing the message text
        LevelRole: Custom role for accessing the log level (as LogLevel enum)
        TimeRole: Custom role for accessing the timestamp
        DurationRole: Custom role for accessing the duration between log entries
    """
    
    # Custom roles for data access
    LineRole = Qt.UserRole + 1      # Message text
    LevelRole = Qt.UserRole + 2     # Log level (LogLevel enum)
    TimeRole = Qt.UserRole + 3      # Timestamp (HH:MM:SS)
    DurationRole = Qt.UserRole + 4  # Duration in seconds since previous timestamped line
    
    # Mapping from string log levels to enum values
    _LEVEL_MAP = {
        'trace': LogLevel.TRACE,
        'debug': LogLevel.DEBUG,
        'info': LogLevel.INFO,
        'warning': LogLevel.WARNING,
        'warn': LogLevel.WARNING,
        'error': LogLevel.ERROR,
        'critical': LogLevel.CRITICAL,
        'fatal': LogLevel.FATAL,
    }
    
    def __init__(self, parent=None):
        """
        Initialize the LogLinesModel.
        
        Args:
            parent: Optional parent QObject
        """
        super().__init__(parent)
        self._lines = []  # List of dictionaries containing parsed log data
        
        # Regex pattern to parse log format: [timestamp][level][optional:numbers] message
        # Groups: 1=time, 2=hours, 3=minutes, 4=seconds, 5=level, 6=optional1, 7=optional2, 8=message
        self._format_regex = re.compile(r'^\[[^]]*?((\d{2}):(\d{2}):(\d{2}))[^]]*\]\[([A-Za-z]+)\](?:\[(\d+):(\d+)\])?\s*(.*)$')
    
    def rowCount(self, parent=QModelIndex()):
        """
        Return the number of rows in the model.
        
        Args:
            parent: Parent index (unused, as this is a flat list model)
            
        Returns:
            int: Number of log lines in the model
        """
        if parent.isValid():
            return 0
        return len(self._lines)
    
    def data(self, index, role=Qt.DisplayRole):
        """
        Retrieve data for a given index and role.
        
        Args:
            index: QModelIndex for the requested item
            role: The data role being requested
            
        Returns:
            The requested data, or None if invalid index or role
        """
        if not index.isValid() or index.row() >= len(self._lines):
            return None
        
        item = self._lines[index.row()]
        
        if role == self.LineRole or role == Qt.DisplayRole:
            return item["line"]
        elif role == self.LevelRole:
            return item["level"]  # Returns LogLevel enum value (int)
        elif role == self.TimeRole:
            return item["time"]
        elif role == self.DurationRole:
            return item["duration"]
        
        return None
    
    def roleNames(self):
        """
        Define role names for QML access.
        
        Returns:
            dict: Mapping of role IDs to byte-encoded role names
        """
        return {
            self.LineRole: b"line",
            self.LevelRole: b"level",
            self.TimeRole: b"time",
            self.DurationRole: b"duration"
        }
    
    @Slot(str)
    def setText(self, text):
        """
        Parse log text and update the model with lines and durations.
        
        This method:
        1. Splits the input text into lines
        2. Parses each line to extract metadata (time, level, message)
        3. Calculates duration between consecutive timestamped lines
        4. Updates the model with the parsed data
        
        Args:
            text: Multi-line string containing log entries
        """
        self.beginResetModel()
        
        self._lines = []
        if not text:
            self.endResetModel()
            return
        
        # Split text into individual lines
        lines = text.split('\n')
        
        
        # Calculate durations between consecutive timestamped lines
        prev_seconds = -1
        for line in lines:
            delta = -1
            
            metadata = self.parseMetadata(line)
            
            seconds = metadata["seconds"]
            if seconds >= 0:
                if prev_seconds >= 0:
                    delta = seconds - prev_seconds
                prev_seconds = seconds
            
            self._lines.append({
                "line": metadata["line"],
                "time": metadata["time"],
                "level": int(metadata["level"]),
                "duration": delta
            })
        
        self.endResetModel()
    
    def parseMetadata(self, line):
        """
        Parse a single log line to extract metadata.
        
        Expected format: [HH:MM:SS][LEVEL][optional:numbers] message
        
        Args:
            line: A single line of log text
            
        Returns:
            dict: Parsed metadata with keys:
                - line (str): The message text
                - time (str): Timestamp in HH:MM:SS format
                - seconds (int): Total seconds since midnight (for duration calculation)
                - level (LogLevel): Log level as enum value
        """
        text = line
        time = "00:00:00"
        level = LogLevel.INFO
        seconds = -1
        
        match = self._format_regex.match(line)
        if match:
            # Extract matched groups
            time = match.group(1)      # HH:MM:SS
            level_str = match.group(5).lower()  # Log level string
            text = match.group(8)      # Message text
            
            # Convert string level to enum
            level = self._LEVEL_MAP.get(level_str, LogLevel.UNKNOWN)

            # Convert time to total seconds for duration calculation
            try:
                hh = int(match.group(2))  # Hours
                mm = int(match.group(3))  # Minutes
                ss = int(match.group(4))  # Seconds
                seconds = ss + 60 * mm + 3600 * hh
            except ValueError:
                # If conversion fails, keep seconds at -1 (Sentinel value)
                pass
        
        return {
            "line": text,
            "time": time,
            "seconds": seconds,
            "level": level
        }
    
    @Slot(result=int)
    def count(self):
        """
        Return the number of lines in the model.
        
        This is a convenience method for QML compatibility.
        
        Returns:
            int: Number of log lines
        """
        return len(self._lines)
    
    @Slot(int, result='QVariant')
    def get(self, index):
        """
        Get the item at the specified index.
        
        This method provides QML-style access similar to ListModel.get().
        
        Args:
            index: The index of the item to retrieve
            
        Returns:
            dict: The item data if index is valid, None otherwise
        """
        if 0 <= index < len(self._lines):
            return self._lines[index]
        return None
    
    @Slot()
    def clear(self):
        """
        Clear all lines from the model.
        
        This removes all log entries and resets the model to an empty state.
        """
        self.beginResetModel()
        self._lines = []
        self.endResetModel()
    
    @Slot(int, result=str)
    def levelToString(self, level):
        """
        Convert a LogLevel enum value to its string representation.
        
        Useful in QML for displaying log level names.
        
        Args:
            level: LogLevel enum value
            
        Returns:
            str: String representation of the log level
        """
        try:
            return LogLevel(level).name
        except ValueError:
            return "UNKNOWN"