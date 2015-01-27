import os

from utils.packrat_backend import PackratBackend


class FilesystemCache(PackratBackend):
    """
    Used to keep track of supported storage backends for packrat. If you would like to add support
    for a new database
    """
    def __init__(self, cache_location):
        super(FilesystemCache, self).__init__(cache_location)
        self.files = {}

    def _create_root_directory(self, cache_path):
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)