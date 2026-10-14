from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional
from pathlib import Path


class PluginServiceError(Exception):
    """
    Raised when a plugin service fails.
    The message reports which service failed, on which plugin, at which step, and why.
    """

    def __init__(self, serviceName: str, pluginName: str, step: str, message: str, exc: Optional[Exception] = None):
        """
        Args:
            serviceName: the name of the service that failed (e.g. "installation").
            pluginName: the name of the plugin the service was working on.
            step: the step of the service that failed (e.g. "download").
            message: what went wrong.
            exc: the exception at the origin of the failure, if any.
        """
        self.error = message
        formattedExc = (f"\n  {type(exc).__name__}: {exc}") if exc else ""
        formattedMessage = (
            f"Plugin {serviceName} failed\n"
            f"  Plugin: {pluginName}\n"
            f"  Step:   {step}\n"
            f"  Error:  {message}"
            f"{formattedExc}"
        )
        super().__init__(formattedMessage)


class PluginServiceCancelled(Exception):
    """
    Raised when a plugin service is cancelled by the user.
    Not an error: the service stopped on request, after having cleaned up after itself.
    """

    def __init__(self, serviceName: str, pluginName: str):
        """
        Args:
            serviceName: the name of the service that was cancelled (e.g. "installation").
            pluginName: the name of the plugin the service was working on.
        """
        formattedMessage = (
            f"Plugin {serviceName} cancelled by user\n"
            f"  Plugin: {pluginName}\n"
        )
        super().__init__(formattedMessage)


# Called by a service to report its progress, with a message and the overall progress (from 0 to 1).
ProgressCallback = Optional[Callable[[str, float], None]]

# Called by a service to know whether it has been cancelled.
CancelChecker = Optional[Callable[[], bool]]


class PluginService(ABC):
    """
    Base class of the services acting on a single plugin (e.g. installation, uninstallation).

    A service is a single command: "execute" runs it from start to finish. It either completes,
    fails, or is cancelled.
    """

    def __init__(self, serviceName: str, pluginName: str, pluginsPath: Path) -> None:
        """
        Args:
            serviceName: the name of the service, used in its errors (e.g. "installation").
            pluginName: the name of the plugin the service acts on.
            pluginsPath: the folder the local plugins are installed in.
        """
        self._serviceName: str = serviceName
        self._pluginName: str = pluginName
        self._pluginsPath: Path = pluginsPath
        self._onProgress: ProgressCallback = None
        self._isCancelled: CancelChecker = None

    def execute(self, onProgress: ProgressCallback = None, isCancelled: CancelChecker = None) -> None:
        """
        Run the service.

        Args:
            onProgress: called with a message and the overall progress (from 0 to 1), each time it changes.
            isCancelled: called regularly, the service is cancelled as soon as it returns True.

        Raises:
            PluginServiceError: if the service fails.
            PluginServiceCancelled: if the service is cancelled.
        """
        self._onProgress = onProgress
        self._isCancelled = isCancelled
        self._run()

    @abstractmethod
    def _run(self) -> None:
        """ The work of the service. """
        raise NotImplementedError

    def _reportProgress(self, message: str, percent: float) -> None:
        """
        Report the progress of the service to the "onProgress" callback, if any.

        Args:
            message: what the service is currently doing.
            percent: the overall progress of the service, from 0 to 1.
        """
        if self._onProgress:
            self._onProgress(message, percent)

    def _checkCancel(self) -> None:
        """ Stop the service if it has been cancelled. """
        if self._isCancelled and self._isCancelled():
            raise PluginServiceCancelled(self._serviceName, self._pluginName)

    def _error(self, step: str, message: str, exc: Optional[Exception] = None) -> PluginServiceError:
        """
        Build the PluginServiceError to raise when a step of the service fails.

        Args:
            step: the step that failed (e.g. "download").
            message: what went wrong.
            exc: the exception at the origin of the failure, if any.

        Returns:
            PluginServiceError: the error, to be raised by the caller.
        """
        return PluginServiceError(self._serviceName, self._pluginName, step, message, exc)

    def _requireInstalledFolder(self) -> Path:
        """
        Return the folder of the installed plugin this service acts on ("<pluginsPath>/<pluginName>").
        """
        pluginFolder = self._pluginsPath / self._pluginName
        if not pluginFolder.is_dir():
            raise self._error("Verification", f"Plugin folder '{pluginFolder}' does not exist.")
        return pluginFolder
