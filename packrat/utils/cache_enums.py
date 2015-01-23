from enum import Enum

class CacheEnums(Enum):
    """
    Used as a utility class for file_cache.py. Contains enums used as success and failure
    indicators internally.
    """
    UPDATED_KEY_SUCCESSFULLY = 1  # Used if a given key is already in the cache.
    ADDED_KEY_SUCCESSFULLY = 2  # Used if a given key is not already in the cache.
    FAILED_TO_ADD_METADATA = 3  # Used if the metadata is not added successfully.
    FILE_TOO_LARGE = 4  # Used if the user-supplied file is too large.
    REMOVAL_ERROR = 5  # Used if an error occurs while removing a key/value pair.
    ADDED_TO_CACHE = 6  # Indicates a file has sucessfully been added to the cache.
    CACHE_ADD_FAILURE = 7  # Used to indicate there was an error adding to the backend.
    INVALID_KEY = 8  # Used to indicate the key was not found in the cache.
    FOUND_IN_CACHE = 9  # Used by the backend filesystem to indicate a successful retrieval.
    REMOVED_SUCCESSFULLY = 10  # Used to indicate a file was successfully removed in the backend.
    FAILED_TO_CLEAR_CACHE = 11  # Used to indicate a problem clearing the cache
    CLEARED_CACHE = 12  # Used to indicate the cache was cleared successfuly
    UNEXPECTED_CODE_PATH = 13