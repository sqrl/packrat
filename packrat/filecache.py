from collections import OrderedDict

from flask import jsonify

DEFAULT_CACHE_SIZE = 10 * 1024 * 1024

class FileCache(object):
    """
    A cache that stores its files on the local filesystem in a directory.
    """
