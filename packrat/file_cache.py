from time import time

from flask import jsonify
import shelve

from utils.cache_codes import CacheCodes
from utils.file_metadata import FileMetadata
from utils.ordered_set import OrderedSet
from utils.supported_backends import SupportedBackends
from utils.backend_names import BackendNames


DEFAULT_CACHE_SIZE = 10 * 1024 * 1024
DEFAULT_DB_PATH = '/tmp/database.db'

# TODO major design concerns:
# - Concurrency issues around read/write
# - Is there a use case where we would want multiple databases? This would be an easy extension
# - Research correct errors to throw in each case. Decide between errors in this module vs.
#   returning error json
# - If the database already exists, how to we decide what lives in it? This seems to be a valid
#   issue, not quite sure how to resolve it.


class FileCache(object):
    """
    A cache that stores its files on the local filesystem in a directory.
    """
    def __init__(self, max_size=DEFAULT_CACHE_SIZE, database_path=DEFAULT_DB_PATH):
        """
        Initializes the cache. Opens an existing database for the metadata cache if one exists
        at the supplied database_path. If there isn't an existing database at the provided
        location, a new one will be created.

        Args:
            max_size (int): The maximum content to store in the cache. Default size is
                10 * 1024 * 1024 bytes.
            database_path (string): Location of the database to open. Default location is
                /tmp/database.db
        """
        self.max_size = max_size
        self.db = shelve.open(database_path)
        self.ordered_items = OrderedSet()
        self.total_content = 0
        self.files = SupportedBackends.init_cache(backend=BackendNames.FILESYSTEM_CACHE)

    def _clear(self, target=0):
        """
        Removes elements from the cache in LRU fashion until the total size is no more than target.

        Args:
            target (int): The target size.

        Returns:
            FAILED_TO_CLEAR_CACHE if any errors arise removing values from the backend cache.
            CLEARED_CACHE if the cache is successfully cleared.
        """
        while self.total_content > target:
            # First clear the key out of our metadata cache
            key = self.ordered_items.pop()
            metadata = self.db[key]  # Add error check here?
            del self.db[key]
            self.total_content -= metadata.file_size
            # Next, clear it out of the filesystem cache. If we fail here, break and return.
            if self.files.remove_file(key) == CacheCodes.INVALID_KEY:
                return CacheCodes.FAILED_TO_CLEAR_CACHE
        # If we cleared successfully, return a success message.
        return CacheCodes.CLEARED_CACHE

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
            value (type TODO): The file to be stored.

        Returns:
            FILE_TOO_LARGE if the file is bigger than the max cache size.
            FAILED_TO_CLEAR_CACHE if there is a failure clearing out old files to make room for
                the new one.
            CACHE_ADD_FAILURE if there is an error adding the file to the backend.
            FAILED_TO_ADD_METADATA if there is an error adding new metadata.
            FAILED_TO_UPDATE_METADATA if there is an error updating pre-existing metadata.
            UPDATED_METADATA_SUCCESSFULLY if the metadata is successfully updated.
            ADDED_METADATA_SUCCESSFULLY if th metadata is successfully added.
        """
        file_size = self._compute_file_size(value)
        file_name = self._compute_file_name(value)

        # Check to make sure the file will fit in the cache.
        if file_size > self.max_size:
            return CacheCodes.FILE_TOO_LARGE

        # First attempt to clear out the cache LRU style to make room for the new file
        self.total_content += file_size
        if self._clear(self.max_size) == CacheCodes.FAILED_TO_CLEAR_CACHE:
            return CacheCodes.FAILED_TO_CLEAR_CACHE
        # Next, attempt to add the file to the backend storage.
        if self.files.add_file(key, value) == CacheCodes.CACHE_ADD_FAILURE:
            return CacheCodes.CACHE_ADD_FAILURE
        # Now we attempt to add the key metadata
        return self._store_file_metadata(key, file_size, file_name)

    def _store_file_metadata(self, key, file_size, file_name):
        """
        Stores metadata associated with a key including:
            - file size
            - creation time
            - file name
            - last access time

        TODO: Look up more specific errors that may be thrown here.

        Args:
            key (string): A key to store the metadata under.
            fileSize (type TODO): The size of the file.
            fileName (string): The name of the file to store.

        Returns:
            FAILED_TO_UPDATE_METADATA if existing metadata is not successfully updated.
            UPDATED_METADATA_SUCCESSFULLY if existing metadata is successfully updated.
            FAILED_TO_ADD_METADATA if there is an error adding new metadata.
            ADDED_METADATA_SUCCESSFULLY if new metadata is successfully added.
        """
        current_time = time() * 1000

        # If the key is already in the cache, we update it with new metadata
        if key in self.ordered_items:
            try:
                metadata = self.db[key]
                self.total_content -= metadata.file_size
                self.total_content += file_size
                metadata.file_size = file_size
                self.ordered_items.move_to_front(key)
                metadata.last_access_time = current_time
                self.db[key] = metadata
            except OSError:
                return CacheCodes.FAILED_TO_UPDATE_METADATA
            return CacheCodes.UPDATED_METADATA_SUCCESSFULLY
        # If the key was not in the cache, we add it and its metadata
        else:
            try:
                metadata = FileMetadata(file_size, current_time, file_name)
                self.db[key] = metadata
                self.ordered_items.add(key)
                self.total_content += file_size
            except OSError:
                return CacheCodes.FAILED_TO_ADD_METADATA
            return CacheCodes.ADDED_METADATA_SUCCESSFULLY

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
        if store_result == CacheCodes.FILE_TOO_LARGE:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "File too large."
            })
        elif store_result == CacheCodes.FAILED_TO_CLEAR_CACHE:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "Failed to clear cache."
            })
        elif store_result == CacheCodes.CACHE_ADD_FAILURE:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "Failed to add to filesystem cache."
            })
        elif store_result == CacheCodes.FAILED_TO_ADD_METADATA:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "Failed to add cache metadata."
            })
        elif store_result == CacheCodes.FAILED_TO_UPDATE_METADATA:
            return jsonify({
                'success': False,
                'error': 413,
                'message': "Failed to add cache metadata."
            })
        elif (store_result == CacheCodes.ADDED_METADATA_SUCCESSFULLY or
              store_result == CacheCodes.UPDATED_METADATA_SUCCESSFULLY):
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
        return metadata.file_name, data

    def status(self):
        """
        Gets some diagnostic information about data stored in the system.

        Returns:
            The number of files stored, the space consumed, and the total cache size.
        """
        return len(self.ordered_items), self.total_content, self.max_size
