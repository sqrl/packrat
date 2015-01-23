import subprocess
import os

from utils.cache_enums import CacheEnums as Enums

DEFAULT_LOCATION = '/tmp/packrat'


class FileBackend():
    """
    A fake class to temporarily stand in for the storage backend and give
    a rudimentary idea of what the API will look like.
    """
    def __init__(self, cache_path=DEFAULT_LOCATION):
        self.files = {}
        self._create_root_directory(cache_path)

    @staticmethod
    def _create_root_directory(cache_path):
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)

    def add_file(self, key, value):
        self.files[key] = value
        return Enums.ADDED_TO_CACHE

    def remove_file(self, key):
        if key not in self.files:
            return Enums.INVALID_KEY
        del self.files[key]
        return Enums.REMOVED_SUCCESSFULLY

    def get_file(self, key):
        if key not in self.files:
            return Enums.INVALID_KEY
        return Enums.FOUND_IN_CACHE, self.files[key]