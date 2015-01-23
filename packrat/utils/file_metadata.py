# TODO: consider concurrency issues on updating access time
class FileMetadata():
	def __init__(self, fileSize, creationTime, fileName):
		self.dict = {'fileSize': fileSize,
					'creationTime': creationTime,
					'lastAccessTime': creationTime,
					'fileName': fileName}
		
	def getCreationTime(self):
		return self.dict['creationTime']

	def getLastAccessTime(self):
		return self.dict['lastAccessTime']

	def getFileSize(self):
		return self.dict['fileSize']

	def updateAccessTime(self, newTime):
		self.dict['lastAccessTime'] = newTime

	def updateFileSize(self, fileSize):
		self.dict['fileSize'] = fileSize

	def getFileName(self):
		return self.dict['fileName']