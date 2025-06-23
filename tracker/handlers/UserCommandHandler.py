class UserCommandHandler:
	def __init__(self, user_repo, peer_repo, send_response_func):
		self.user_repo = user_repo
		self.peer_repo = peer_repo
		self.send_response = send_response_func
	
	def login(self, conn, data):
		username = data.get("username")
		password = data.get("password")
		address = data.get("address")
		port = data.get("port")
		
		if self.user_repo.validate_user(username, password):
			self.peer_repo.update_connection(username, address, port)
			self.send_response(conn, "OK", "Login realizado com sucesso.")
		else:
			self.send_response(conn, "ERROR", "Credenciais inválidas.")
	
	def register(self, conn, data):
		username = data.get("username")
		password = data.get("password")
		address = data.get("address")
		port = data.get("port")
		
		if self.user_repo.user_exists(username):
			self.send_response(conn, "ERROR", "Usuário já existe.")
		else:
			self.user_repo.create(username, password)
			self.peer_repo.update_connection(username, address, port)
			self.send_response(conn, "OK", "Usuário registrado com sucesso.")
