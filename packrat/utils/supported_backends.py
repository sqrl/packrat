from enum import Enum

from utils.filesystem_cache import FilesystemCache
from utils.backend_names import BackendNames


DEFAULT_LOCATION = '/tmp/packrat'


class SupportedBackends():
    """
    Defines the various init methods for supported backends. If you want to add support for a new
    backend, you must add support for a new init method here.
    """
    @staticmethod
    def init_cache(backend=BackendNames.FILESYSTEM_CACHE, cache_location=DEFAULT_LOCATION):
        if backend == BackendNames.FILESYSTEM_CACHE:
            return SupportedBackends._init_filesystem_cache(cache_location)
        else:
            raise UnsupportedBackendError("Unsupported backend: %s" % backend)

    @staticmethod
    def _init_filesystem_cache(cache_location):
        return FilesystemCache(cache_location)


class UnsupportedBackendError(Exception):
    """
    Defines an error arising from an unsupported backend.
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
