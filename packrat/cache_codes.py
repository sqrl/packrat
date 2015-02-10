from enum import Enum


class CacheCodes(Enum):
    """
    Used as a utility class for file_cache.py. Contains enums used as success and failure
    indicators internally.
    """
    # Enums related to adding key metadata.
    UPDATED_METADATA_SUCCESSFULLY = 1  # Used if a given key is already in the cache.
    FAILED_TO_UPDATE_METADATA = 2  # Used to indicate failure updating metadata.
    ADDED_METADATA_SUCCESSFULLY = 3  # Used if a given key is not already in the cache.
    FAILED_TO_ADD_METADATA = 4  # Used if the metadata is not added successfully.
    FILE_TOO_LARGE = 5  # Used if the user-supplied file is too large.
    REMOVAL_ERROR = 6  # Used if an error occurs while removing metadata.

    # Enums related to backend operations
    ADDED_TO_CACHE = 7  # Indicates a file has successfully been added to the cache.
    CACHE_ADD_FAILURE = 8  # Used to indicate there was an error adding to the backend.
    INVALID_KEY = 9  # Used to indicate the key was not found in the cache.
    REMOVED_SUCCESSFULLY = 10  # Used to indicate a file was successfully removed in the backend.
    FAILED_BACKEND_REMOVAL = 11  # Used to indicate an error removing a file from the backend
    FOUND_IN_CACHE = 12  # Used by the backend filesystem to indicate a successful file retrieval.
    FAILED_BACKEND_RETRIEVAL = 13  # Used by the backend to indicate failure to retrieve file.

    # Used to indicate success/failure when clearing the cache LRU style.
    CLEARED_CACHE = 14  # Used to indicate the cache was cleared successfully
    FAILED_TO_CLEAR_CACHE = 15  # Used to indicate a problem clearing the cache

    # Used to indicate something went very wrong
    UNEXPECTED_CODE_PATH = 16
