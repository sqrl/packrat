from collections import OrderedDict

from flask import jsonify

DEFAULT_CACHE_SIZE = 10 * 1024 * 1024


class MemoryCache(object):
    """
    A cache for packrat that stores all file uploads in memory.  Useful for testing.
    """
    def __init__(self, max_size=DEFAULT_CACHE_SIZE):
        """
        Initializes the cache.

        Args:
            max_size (int): The maximum content to store in the cache.
        """
        self.max_size = max_size
        self.files = OrderedDict([])
        self.total_content = 0


    def _clear(self, target=0):
        """
        Removes elements from the cache in LRU fashion until the total size is no more than target.

        Args:
            target (int): The target size.
        """
        while self.total_content > target:
            item = self.files.popitem(last=False)
            self.total_content = self.total_content - item['size']


    def store_file(self, key, file):
        """
        Attempts to add a file to the cache.

        Args:
            key (string): The key to store the file under. Will replace any existing
                file stored under this key.
            file (FileStorage): A Flask FileStorage object representing the temporary
                file received from HTTP.

        Returns:
            A json record indicating success or failure (if an error occurred or the
            file was too large to fit in the cache, for example).
        """
        if not key:
            return jsonify({
                'success': False,
                'error': 500,
                'message': "Unexpected invalid key."
            })

        temp = file.read()
        if len(temp) > self.max_size:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "File too large."
            })
        if key in self.files:
            self.total_content = self.total_content - self.files[key]['size']
            del self.files[key]


        self._clear(self.max_size - len(temp))
        self.files[key] = {
            'size': len(temp),
            'filename': file.filename,
            'data': temp
        }
        self.total_content += len(temp)
        return jsonify({
            'success': True,
            'message': ("Uploaded under %s. %d bytes remain."
                        % (key, self.max_size - self.total_content))
        })


    def get_file(self, key):
        """
        Retrieves a file stored under a key.

        Args:
            key (string): The key to look up.

        Returns:
            A tuple with the filename and the contents of the file as a string
            or None if it's not found.
        """
        if not key in self.files:
            return None
        self.files.move_to_end(key)
        return self.files[key]['filename'], self.files[key]['data']

    def status(self):
        """
        Gets some diagnostic information about data stored in the system.

        Returns:
            The number of files stored, the space consumed, and the total cache size.
        """
        return len(self.files), self.total_content, self.max_size
