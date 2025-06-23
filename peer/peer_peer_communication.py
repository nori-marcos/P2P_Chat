import json
import socket
import threading


class PeerPeerCommunication:
	def __init__(self, host="localhost", port=0):
		self.host = host
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.host, self.port))
		self.socket.listen()
		self.actual_address, self.actual_port = self.socket.getsockname()
		self.running = True
		self.connections = {}
	
	def peer_connection(self, conn):
		try:
			data = conn.recv(1024).decode("utf-8")
			message = json.loads(data)
			cmd = message.get("cmd")
			
			if cmd == "HELLO":
				username = message.get("username")
				print(f"[CONEXÃO] {username} se conectou.")
				self.connections[username] = conn
				threading.Thread(target=self.receive_messages, args=(conn, username), daemon=True).start()
			elif cmd == "PING":
				print("[TRACKER] Ping recebido.")
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
				print(f"[ENTRADA] Conexão de: {addr}")
				threading.Thread(target=self.peer_connection, args=(conn,), daemon=True).start()
			except Exception as e:
				print(f"[ERRO] {e}")
	
	def connect_to_peer(self, peer_info, from_username):  # Pass your own username
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(5)
			s.connect((peer_info["address"], peer_info["port"]))
			
			hello_msg = json.dumps({
					"cmd": "HELLO",
					"username": from_username
			}).encode("utf-8")
			s.send(hello_msg)
			
			self.connections[peer_info["username"]] = s
			threading.Thread(target=self.receive_messages, args=(s, peer_info["username"]), daemon=True).start()
			print(f"[CONECTADO] com {peer_info['username']}")
		except Exception as e:
			print(f"[FALHA] ao conectar com {peer_info['username']}: {e}")
	
	def receive_messages(self, conn, username):
		try:
			while self.running:
				data = conn.recv(1024)
				if not data:
					print(f"[INFO] Conexão com {username} foi fechada.")
					break
				
				message = json.loads(data.decode("utf-8"))
				command = message.get("cmd")
				room = message.get("room")
				
				if command == "MESSAGE":
					content = message.get('content')
					if room is not None:
						print(f"[MENSAGEM na sala {room} de {username}] {content}")
					else:
						print(f"[MENSAGEM de {username}] {content}")
				elif command == "LEAVE":
					print(f"[INFO] {username} saiu da sala.")
					break
		
		except Exception as e:
			print(f"[ERRO] ao receber mensagem de {username}: {e}")
		finally:
			print(f"[DESCONECTADO] de {username}.")
			conn.close()
			if username in self.connections:
				del self.connections[username]
	
	def send_message(self, room_name, to_username, from_username, content):
		conn = self.connections.get(to_username)
		if conn:
			try:
				conn.send(json.dumps({
						"cmd": "MESSAGE",
						"room": room_name,
						"from": f"{self.actual_address}:{self.actual_port}",
						"username": from_username,
						"content": content
				}).encode("utf-8"))
			except Exception as e:
				print(f"[ERRO] ao enviar mensagem para {to_username}: {e}")
		else:
			print(f"[AVISO] Conexão com {to_username} não encontrada.")
	
	def leave_room(self, peers_in_room: list):
		leave_message = json.dumps({"cmd": "LEAVE"}).encode("utf-8")
		
		for peer_username in peers_in_room:
			conn = self.connections.get(peer_username)
			if conn:
				try:
					print(f"[SAINDO] Notificando {peer_username}...")
					conn.send(leave_message)
				except Exception as e:
					print(f"[ERRO] Falha ao notificar {peer_username}: {e}")
				finally:
					conn.close()
					del self.connections[peer_username]
	
	def close(self):
		self.running = False
		for conn in self.connections.values():
			try:
				conn.close()
			except:
				pass
		self.socket.close()
