from abc import ABCMeta, abstractmethod


class PackratBackend():
    """
    An abstract base class that defines the API packrat will use to communicate with its backend
    file storage. Any new backend implementations must override the methods provided here.
    """

    __metaclass__ = ABCMeta

    def __init__(self, cache_path):
        pass
        self._create_root_directory(cache_path)

    @abstractmethod
    def _create_root_directory(self, cache_path):
        pass

    @abstractmethod
    def add_file(self, key, value):
        """
        Adds the file to the backend storage.

        Args:
            key: They key to store/retrieve the file.
            value: The file itself.
        Returns:
            ADDED_TO_CACHE if the file is successfully added.
            CACHE_ADD_FAILURE if the file is not successfully added.
        """
        pass


    @abstractmethod
    def remove_file(self, key):
        """
        Removes the file from the backend storage.

        Args:
            key: The key to store/retrieve the file.
        Returns:
            INVALID_KEY if the key does not exist in the backend.
            FAILED_BACKEND_REMOVAL if there is a failure removing the file.
            REMOVED_SUCCESSFULLY if the file is successfully removed.
        """
        pass

    @abstractmethod
    def get_file(self, key):
        """
        Get the file associated with the provided key from the backend storage.

        Args:
            key: They key to store/retrieve the file
        Returns:
            (INVALID_KEY, None) if the key does not exist in the backend.
            (FAILED_BACKEND_RETRIEVAL, None) if there is a retrieval error in the backend.
            (FOUND_IN_CACHE, file) if the file is successfully retrieved.
        """
        pass
        # if key not in self.files:
        #     return Enums.INVALID_KEY
        # return Enums.FOUND_IN_CACHE, self.files[key]