class FileMetadata():
    def __init__(self, file_size, creation_time, file_name):
        self.file_size = file_size
        self.creation_time = creation_time
        self.last_access_time = creation_time
        self.file_name = file_name
