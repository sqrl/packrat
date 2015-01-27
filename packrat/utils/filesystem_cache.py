import os

from utils.packrat_backend import PackratBackend


class FilesystemCache(PackratBackend):
    """
    Implementation of a Filesystem Cache. Not implemented yet.
    """
    def __init__(self, cache_location):
        super(FilesystemCache, self).__init__(cache_location)
        self.files = {}

    # TODO: it seems weird to make this necessary to override
    def _create_root_directory(self, cache_path):
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

    def add_file(self, key, value):
        self.files[key] = value

    def remove_file(self, key):
        del self.files[key]

    def get_file(self, key):
        return self.files[key]
