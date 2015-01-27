from enum import Enum


class BackendNames(Enum):
    """
    The types of backends supported by packrat. If you want to add support for a new backend, the
    name here must match the backend class name.

    TODO: I would love to move this class in to packrat_backend but for some reason am unable to
        access it there...
    """
    FILESYSTEM_CACHE = 1
