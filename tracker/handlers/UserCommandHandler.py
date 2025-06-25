class UserCommandHandler:
	def __init__(self, user_repo, peer_repo, send_response_func):
		self.user_repo = user_repo
		self.peer_repo = peer_repo
	
	def login(self, data) -> bool:
		username = data.get("username")
		password = data.get("password")
		address = data.get("address")
		port = data.get("port")
		
		if self.user_repo.validate_user(username, password):
			self.peer_repo.update_connection(username, address, port)
			return True
		else:
			return False
	
	def register(self, data) -> bool:
		username = data.get("username")
		password = data.get("password")
		address = data.get("address")
		port = data.get("port")
		
		if self.user_repo.user_exists(username):
			return False
		else:
			self.user_repo.create(username, password)
			self.peer_repo.update_connection(username, address, port)
			return True
