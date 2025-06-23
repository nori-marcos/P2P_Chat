import json
import socket
import threading


class PeerPeerCommunication:
	def __init__(self, host="localhost", port=0, message_callback=None):
		self.host = host
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.host, self.port))
		self.socket.listen()
		self.actual_address, self.actual_port = self.socket.getsockname()
		self.running = True
		self.connections = {}
		self.on_message_received = message_callback
	
	def peer_connection(self, conn):
		try:
			data = conn.recv(1024).decode("utf-8")
			message = json.loads(data)
			cmd = message.get("cmd")
			
			if cmd == "HELLO":
				username = message.get("username")
				print(f"[CONEXÃO P2P] {username} se conectou.")
				self.connections[username] = conn
				threading.Thread(target=self.receive_messages, args=(conn, username), daemon=True).start()
			elif cmd == "PING":
				conn.send(json.dumps({"cmd": "PONG"}).encode("utf-8"))
				conn.close()
			else:
				print(f"[PEER] Conexão recebida com comando inesperado: {cmd}")
				conn.close()
		
		except Exception as e:
			print(f"[ERRO] na conexão com peer/tracker: {e}")
			conn.close()
	
	def listen_for_peers(self):
		while self.running:
			try:
				conn, addr = self.socket.accept()
				threading.Thread(target=self.peer_connection, args=(conn,), daemon=True).start()
			except Exception as e:
				if self.running:
					print(f"[ERRO] na escuta de peers: {e}")
	
	def connect_to_peer(self, peer_info, from_username):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(5)
			s.connect((peer_info["address"], peer_info["port"]))
			
			s.settimeout(None)
			
			hello_msg = json.dumps({
					"cmd": "HELLO",
					"username": from_username
			}).encode("utf-8")
			s.send(hello_msg)
			
			self.connections[peer_info["username"]] = s
			threading.Thread(target=self.receive_messages, args=(s, peer_info["username"]), daemon=True).start()
			print(f"[CONECTADO P2P] com {peer_info['username']}")
		except Exception as e:
			print(f"[FALHA] ao conectar com {peer_info['username']}: {e}")
	
	def receive_messages(self, conn, username):
		try:
			while self.running:
				data = conn.recv(4096)
				if not data:
					print(f"[INFO] Conexão com {username} foi fechada por ele(a).")
					break
				
				message = json.loads(data.decode("utf-8"))
				command = message.get("cmd")
				
				if self.on_message_received:
					self.on_message_received(command, username, message)
				
				if command == "LEAVE":
					break
		
		except Exception as e:
			print(f"[ERRO] ao receber mensagem de {username}: {e}")
		finally:
			print(f"[DESCONECTADO P2P] de {username}.")
			conn.close()
			if username in self.connections:
				del self.connections[username]
	
	def send_message(self, room_name, to_username, from_username, content) -> bool:
		conn = self.connections.get(to_username)
		if conn:
			try:
				message_to_send = {
						"cmd": "MESSAGE",
						"room": room_name,
						"username": from_username,
						"content": content
				}
				conn.sendall(json.dumps(message_to_send).encode("utf-8"))
				return True
			except (BrokenPipeError, ConnectionResetError) as e:
				print(f"[ERRO] Conexão com {to_username} foi perdida: {e}")
				self.cleanup_connection(conn, to_username)
				return False
			except Exception as e:
				print(f"[ERRO] ao enviar mensagem para {to_username}: {e}")
				return False
		else:
			print(f"[AVISO] Conexão com {to_username} não encontrada.")
			return False
	
	def leave_room(self, peers_in_room: list):
		leave_message = json.dumps({"cmd": "LEAVE"}).encode("utf-8")
		
		for peer_username in peers_in_room:
			if peer_username in self.connections:
				conn = self.connections.get(peer_username)
				try:
					print(f"[SAINDO] Notificando {peer_username}...")
					conn.send(leave_message)
				except Exception as e:
					print(f"[ERRO] Falha ao notificar {peer_username}: {e}")
				finally:
					self.cleanup_connection(conn, peer_username)
	
	def cleanup_connection(self, conn, username):
		if conn:
			conn.close()
		if username in self.connections:
			del self.connections[username]
	
	def close(self):
		self.running = False
		for username, conn in list(self.connections.items()):
			self.cleanup_connection(conn, username)
		self.socket.close()
