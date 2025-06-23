class User:
	def __init__(self, username: str, password: str):
		self.username = username
		self.password = password
	
	def to_dict(self):
		return self.password
	
	@staticmethod
	def from_dict(username, password):
		return User(username, password)
