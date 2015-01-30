import atexit
import collections.namedtuple
import os
import shelve

from flask import jsonify

from utils.cache_codes import CacheCodes


DEFAULT_CACHE_SIZE = 10 * 1024 * 1024
""" The default cache max-size. """

DEFAULT_DB_PATH = '/tmp/packrat-storage'
""" The default location to store uploaded files and their metadata. """

_SHELVE_FILENAME = "packrat-md.shelve" # Name of file under the storage path that holds metadata.
_SHELVE_CACHE_KEY = "lru_cache" # Key used to store our LRU cache metadata in our shelve file.
_DB_SUBDIRECTORY = # The name of the subdirectory where actual files are stored, named after their keys.

# TODO major design concerns:
# - Concurrency issues around read/write. (We can solve these maybe with gevent.)
# - Is there a use case where we would want multiple databases? This would be an easy extension.
#   (Probably not?)
# - Research correct errors to throw in each case. Decide between errors in this module vs.
#   returning error json. (We should have json errors in a separate file.)
# - If the databa[se already exists, how to we decide what lives in it? This seems to be a valid
#   issue, not quite sure how to resolve it. (We should have a separate execution mode for what
#   is effectively fsck).

_FileMetadata = collections.namedtuple('_FileMetaData', ['key', 'filename', 'size'])


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
                /tmp/packrat-storage.
        """
        self.max_size = max_size
        os.makedirs(database_path, exist_ok=True)
        self.database_path = database_path
        self.db = shelve.open(os.path.join(database_path, _SHELVE_FILENAME))
        self.ordered_items = self.db.get(_SHELVE_CACHE_KEY, [])
        self.total_content = 0
        for entry in self.ordered_items:
            self.total_content += entry.size
        atexit.register(self._close_db())

    def _close_db(self):
        """
        Closes the shelve db. Designed to be used as a shutdown hook and should not be called
        directly.

        Returns:
            None
        """
        self.db.close()


    def _save_metadata(self):
        """
        Saves the metadata into the shelve file. Until this call completes, changes to the
        metadata list will not be persisted.

        Returns:
            None
        """
        self.db[_SHELVE_CACHE_KEY] = self.ordered_items

    def _filename_for_key(self, key):
        """
        Given a file key, returns the filename (including path) for where that key
        should be on disk.

        Args:
            key (str): The key as a string.

        Returns:
            (string) The filename including path (possibly relative) if `database_path`
                was relative.
        """
        return os.path.join(self.database_path, _DB_SUBDIRECTORY, key)

    def _add_file(self, key, file):
        """
        Main function used internally for storing the file. There are two main operations being
        performed here:
            1. Storing the file data on the backend filesystem cache.
            2. Storing the file metadata in a lightweight database managed by the shelve module.

        Args:
            key (string): The key to be stored.
            file (FileStorage): A Flask FileStorage object to be saved.

        Returns:
            FAILED_TO_CLEAR_CACHE if there is a failure clearing out old files to make room for
                the new one.
            CACHE_ADD_FAILURE if there is an error adding the file to the backend.
            FAILED_TO_ADD_METADATA if there is an error adding new metadata.
            FAILED_TO_UPDATE_METADATA if there is an error updating pre-existing metadata.
            UPDATED_METADATA_SUCCESSFULLY if the metadata is successfully updated.
            ADDED_METADATA_SUCCESSFULLY if the metadata is successfully added.
        """
        was_update = False
        # Check to see if we're replacing an existing file. If so, make it unreachable for now.
        # TODO: Consider keeping the older file entry until the copy finishes with a temporary
        # file and a copy command.
        if key in self.ordered_items:
            self.ordered_items.remove(key)
            self._save_metadata()
            was_update = True

        # Save the file to disk. This may take a while so concurrency here is important.
        storage_filename = self._filename_for_key(key)
        file.save(storage_filename)

        client_filename = file.filename # Filename as provided by client.
        size = os.path.getsize(storage_filename)
        metadata = _FileMetadata(key, client_filename, size)

        # Make a list of candidate files to remove from the system.
        to_remove = []
        while self.total_content + size > self.max_size:
            oldest = self.ordered_items.pop(0)
            self.total_content -= oldest.size
            to_remove.append(oldest)

        # Add new metadata to the cache and save the result. This may block and result in a
        # context switch under gevent. At this point the new file is visible and the old
        # ones are not, but we still have to delete the files.
        self.ordered_items.append(metadata)
        self.total_content += size
        self._save_metadata()

        # Now remove the evicted files.
        for file in to_remove:
            # Make sure the file hasn't been added back. This will be important with
            # concurrency: If someone re-uploaded the file, we don't want to delete it.
            if file.key in self.ordered_items:
                continue
            os.remove(self._filename_for_key(file.key))

        if was_update:
            return CacheCodes.UPDATED_METADATA_SUCCESSFULLY
        return CacheCodes.ADDED_METADATA_SUCCESSFULLY

    def store_file(self, key, file):
        """
        Attempts to add a file to the cache.

        Args:
            key (string): The key to store the file under. Will replace any existing
                file stored under this key.
            file (FileStorage): A Flask FileStorage object to be saved.

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

        store_result = self._store_file(key, file)
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
                'message': "Unexpected server error."
            })

    def get_file(self, key):
        """
        Retrieves a file stored  under a key.

        Args:
            key (string): The key to look up.

        Returns:
            A tuple with the filename on disk and filename to return to the client.
        """
        if key not in self.ordered_items:
            return None
        self.ordered_items.move_to_front(key)
        metadata = self.db[key]
        data = self.files.get_filename(key)
        if not data:

        return metadata.file_name, data

    def status(self):
        """
        Gets some diagnostic information about data stored in the system.

        Returns:
            The number of files stored, the space consumed, and the total cache size.
        """
        return len(self.ordered_items), self.total_content, self.max_size
