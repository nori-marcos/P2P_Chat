import json
import socket
import threading
from datetime import datetime, timedelta


class TrackerServer:
	def __init__(self, host='0.0.0.0', port=6060, users_db='users_db.json'):
		self.host = host
		self.port = port
		self.users_db = users_db
		self.users = self.load_users()
		self.peers = {}
		self.login_history = {}
		self.last_ping = {}
	
	"""
	Carrega o arquivo json que contém os usuários e senhas.
	"""
	def load_users(self):
		try:
			with open(self.users_db, "r") as f:
				return json.load(f)
		except FileNotFoundError:
			return {}
	
	"""
	Salva os usuários e senhas no arquivo json.
	"""
	def save_users(self):
		with open(self.users_db, "w") as f:
			json.dump(self.users, f, indent=2)
	
	"""
	Gerencia o login do usuário, verificando se as credenciais estão corretas.
	"""
	def handle_login(self, conn, addr, data):
		user = data.get("user")
		password = data.get("password")
		
		if user in self.users and self.users[user] == password:
			self.peers[user] = addr
			self.login_history[user] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			self.send_response(conn, status="OK", msg="Login realizado com sucesso.")
		else:
			self.send_response(conn, status="ERROR", msg="Credenciais inválidas.")
	
	"""
	Registra um novo usuário, salvando suas credenciais no arquivo json.
	"""
	def handle_register(self, conn, data):
		user = data.get("user")
		password = data.get("password")
		
		if user in self.users:
			self.send_response(conn, status="ERROR", msg="Usuário já existe.")
		else:
			self.users[user] = password
			self.save_users()
			self.send_response(conn, status="OK", msg="Usuário registrado com sucesso.")
	
	"""
	Lista os usuários conectados no tracker.
	"""
	def handle_list_peers(self, conn):
		peer_list = []
		now = datetime.now()
		
		for user in self.peers:
			last = self.last_ping.get(user)
			online = False
			if last:
				online = (now - last) < timedelta(seconds=30)
			
			peer_list.append({
					"user": user,
					"last_login": self.login_history.get(user, "N/A"),
					"status": "online" if online else "offline"
			})
		
		response = {
				"status": "OK",
				"peers": peer_list
		}
		conn.send(json.dumps(response, ensure_ascii=False).encode("utf-8"))
	
	"""
	Envia uma resposta ao cliente com o status e mensagem correspondentes.
	"""
	@staticmethod
	def send_response(conn, status, msg):
		response = {
				"status": status,
				"msg": msg
		}
		conn.send(json.dumps(response, ensure_ascii=False).encode("utf-8"))
	
	"""
	Confirma se o usuário está logado e atualiza o timestamp do último ping.
	"""
	def handle_ping(self, conn, data):
		user = data.get("user")
		if user in self.peers:
			self.last_ping[user] = datetime.now()
			self.send_response(conn, "OK", "Ping recebido.")
		else:
			self.send_response(conn, "ERROR", "Usuário não logado.")
	
	"""
	Gerencia a conexão com o cliente, recebendo comandos e respondendo adequadamente.
	"""
	def handle_client(self, conn, addr):
		try:
			raw = conn.recv(1024).decode("utf-8")
			data = json.loads(raw)
			cmd = data.get("cmd")
			
			if cmd == "LOGIN":
				self.handle_login(conn, addr, data)
			elif cmd == "REGISTER":
				self.handle_register(conn, data)
			elif cmd == "LIST_PEERS":
				self.handle_list_peers(conn)
			else:
				self.send_response(conn, "ERROR", "Comando não suportado.")
		except Exception as e:
			print(f"[ERRO] {addr}: {e}")
			self.send_response(conn, "ERROR", "Erro interno no servidor.")
		finally:
			conn.close()
	
	def start(self):
		print(f"Tracker rodando em {self.host}:{self.port}")
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.bind((self.host, self.port))
		server_socket.listen()
		
		while True:
			conn, addr = server_socket.accept()
			thread = threading.Thread(target=self.handle_client, args=(conn, addr))
			thread.start()


if __name__ == "__main__":
	tracker = TrackerServer()
	tracker.start()
