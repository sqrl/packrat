import shelve
from flask import jsonify
from time import time

from utils.ordered_set import OrderedSet
from utils.file_metadata import FileMetadata
from utils.file_backend import FileBackend
from utils.cache_enums import CacheEnums as Enums

DEFAULT_CACHE_SIZE = 10 * 1024 * 1024
DEFAULT_DB_PATH = '/tmp/database.db'

# TODO major design concerns:
# - Concurrency issues around read/write
# - Does it make sense to always keep the database open? My understanding is that packrat will
#   control all database access, so it could just keep it open always. But this may not make sense.
# - Is there a use case where we would want multiple databases? This would be an easy extension
# - Research correct errors to throw in each case. Decide between errors in this module vs.
#   returning error json
# - Add logic to open already existing database and read the number of files stored there?


class FileCache(object):
    """
    A cache that stores its files on the local filesystem in a directory.
    """
    def __init__(self, max_size=DEFAULT_CACHE_SIZE, database_path=DEFAULT_DB_PATH):
        """
        Initializes the cache. Opens a new database for the metadata cache at the supplied
        database_path. If there isn't a database at the provided location, a new one will be
        created.

        Args:
            max_size (int): The maximum content to store in the cache.
            database_path (string): Location of the database to open.
        """
        self.max_size = max_size
        self.dbInitialized = False
        self.db = shelve.open(database_path)
        self.ordered_items = OrderedSet()
        self.total_content = 0
        self.files = FileBackend()

    def _clear(self, target=0):
        """
        Removes elements from the cache in LRU fashion until the total size is no more than target.

        Args:
            target (int): The target size.

        Returns:
            TODO: Consider possible errors to throw
        """
        while self.total_content > target:
            # First clear the key out of our metadata cache
            key = self.ordered_items.pop()
            metadata = self.db[key]
            self.total_content -= metadata.getFileSize()
            # Next, clear it out of the filesystem cache
            if self.files.remove_file(key) == Enums.INVALID_KEY:
                return Enums.FAILED_TO_CLEAR_CACHE
        return Enums.CLEARED_CACHE

    def _compute_file_size(self, value):
        """
        Computes the size of a file.
        TODO: Implement this. Dependent on deciding what sort of structure the file will be
            passed in with.

        Args:
            file (type TODO): The file to cache.

        Returns:
            (type TODO)The size of the file
        """
        return 1

    def _compute_file_name(self, value):
        """
        Computes the name of a file.
        TODO: Not quite sure what the file name will be used for, or how it will be computed
            and passed in. The main use case I see is for external use. The hope for now is that
            the name can be recovered from the value or key, otherwise the API in memorycache will
            have to be modified for consistency as well.

        Args:
            value (FileType TODO): The file itself.

        Returns:
            (string) The name of the file.
        """
        return "not a real name"

    def _store_file(self, key, value):
        """
        Main function used internally for storing the file. There are two main operations being
        performed here:
            1. Storing the file metadata in a lightweight database managed by the shelve module.
                This metadata is stored with the shelve module, which exposes a dict-like API. The
                keys are also kept in an ordered set that maintains the order of key addition
                for LRU style removal while providing O(1) key lookup.
            2. If storing the file metadata is successful, it will be added to the backend
                filesystem cache.

        Args:
            key (string): The key to be stored.
            value (type TODO): They file to be stored.

        Returns:

        """
        file_size = self._compute_file_size(value)
        file_name = self._compute_file_name(value)

        # Attempt to store the file metadata.
        (store_result, old_metadata) = self._store_file_metadata(key, file_size, file_name)
        # Clear the cache using a LRU heuristic.
        if self._clear(self.max_size) == Enums.FAILED_TO_CLEAR_CACHE:
            return Enums.FAILED_TO_CLEAR_CACHE

        # If we are successful storing the metadata, add it to the backend filesystem cache.
        if (store_result == Enums.UPDATED_KEY_SUCCESSFULLY or
                store_result == Enums.ADDED_KEY_SUCCESSFULLY):
            cache_add_result = self.files.add_file(key, value)
            # If the file is successfully added to the backend, move key to the front of the cache.
            if cache_add_result == Enums.ADDED_TO_CACHE:
                if key in self.ordered_items:
                    self.ordered_items.move_to_front(key)
                else:
                    self.ordered_items.add(key)
                return cache_add_result
            # Otherwise, we return with a failure message and reset to old metadata.
            # TODO: This might not be right, consider case where old data is lost in backend.
            elif cache_add_result == Enums.CACHE_ADD_FAILURE:
                self.db[key] = old_metadata
                return cache_add_result
        # If we are unsuccessful storing the metadata, return the reason for failure.
        elif (store_result == Enums.FILE_TOO_LARGE or
              store_result == Enums.FAILED_TO_ADD_METADATA):
            return store_result
        else:
            return Enums.UNEXPECTED_CODE_PATH

    def _store_file_metadata(self, key, file_size, file_name):
        """
        Stores metadata associated with a key including:
            - file size
            - creation time
            - file name
            - last access time

        Args:
            key (string): A key to store the metadata under.
            fileSize (type TODO): The size of the file.
            fileName (string): The name of the file to store.

        Returns:
            Tuples of (success message, optional data)
            (FILE_TOO_LARGE, None) if the file is too large
            (UPDATED_KEY_SUCCESSFULLY, old file metadata) if the key was already in the cache. The
                old metadata is returned in case the backend add fails and we want to roll back
                to the old key value.
            (ADDED_KEY_SUCCESSFULLY, None) if the key was not in the cache.
        """
        if file_size > self.max_size:
            return Enums.FILE_TOO_LARGE, None

        current_time = time() * 1000

        # If the key is already in the cache, we update it with new metadata
        if key in self.ordered_items:
            old_metadata = metadata = self.db[key]
            self.total_content -= metadata.getFileSize()
            self.total_content += file_size
            metadata.updateFileSize(file_size)
            metadata.updateAccessTime(current_time)
            self.db[key] = metadata
            return Enums.UPDATED_KEY_SUCCESSFULLY, old_metadata
        # If the key was not in the cache, we add it and its metadata
        else:
            metadata = FileMetadata(file_size, current_time, file_name)
            self.db[key] = metadata
            self.total_content += file_size
            return Enums.ADDED_KEY_SUCCESSFULLY, None

    def store_file(self, key, value):
        """
        Attempts to add a file to the cache.

        Args:
            key (string): The key to store the file under. Will replace any existing
                file stored under this key.
            file: TODO determine how file is handled

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

        store_result = self._store_file(key, value)
        if store_result == Enums.FILE_TOO_LARGE:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "File too large."
            })
        elif store_result == Enums.CACHE_ADD_FAILURE:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "Failed to add to filesystem cache."
            })
        elif store_result == Enums.FAILED_TO_ADD_METADATA:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "Failed to add cache metadata."
            })
        elif store_result == Enums.FAILED_TO_CLEAR_CACHE:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "Failed to clear cache."
            })
        elif store_result == Enums.ADDED_TO_CACHE:
            return jsonify({
                'success': True,
                'message': ("Uploaded under %s. %d bytes remain."
                            % (key, self.max_size - self.total_content))
            })
        else:
            return jsonify({
                'success': False,
                'error': 500,
                'message': "Unexpected path."
            })

    def get_file(self, key):
        """
        Retrieves a file stored  under a key.

        Args:
            key (string): The key to look up.

        Returns:
            A tuple with the filename and the contents of the file as a string
            or None if it's not found.
        """
        if key not in self.ordered_items:
            return None
        self.ordered_items.move_to_front(key)
        metadata = self.db[key]
        data = self.files.get_file(key)
        return metadata.getFileName(), data

    def status(self):
        """
        Gets some diagnostic information about data stored in the system.

        Returns:
            The number of files stored, the space consumed, and the total cache size.
        """
        return len(self.ordered_items), self.total_content, self.max_size
