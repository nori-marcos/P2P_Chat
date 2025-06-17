import json
import socket
import threading
import time

from tracker.peer.peer_repository import PeerRepository
from tracker.room.room_repository import RoomRepository
from tracker.user.user_repository import UserRepository

PING_INTERVAL = 120


class TrackerService:
	def __init__(self, host="localhost", port=6060):
		self.host = host
		self.port = port
		self.room_repo = RoomRepository()
		self.peer_repo = PeerRepository()
		self.user_repo = UserRepository()
	
	def send_response(self, conn, status, msg=None, **extra_fields):
		response = {"status": status}
		if msg is not None:
			response["msg"] = msg
		response.update(extra_fields)
		conn.send(json.dumps(response).encode("utf-8"))
	
	def login(self, conn, data):
		username = data.get("username")
		password = data.get("password")
		host = data.get("host")
		port = data.get("port")
		
		if self.user_repo.validate_user(username, password):
			self.peer_repo.update_connection(username, host, port)
			self.send_response(conn, "OK", "Login realizado com sucesso.")
		else:
			self.send_response(conn, "ERROR", "Credenciais inválidas.")
	
	def register(self, conn, data):
		username = data.get("username")
		password = data.get("password")
		host = data.get("host")
		port = data.get("port")
		
		if self.user_repo.user_exists(username):
			self.send_response(conn, "ERROR", "Usuário já existe.")
		else:
			self.user_repo.create(username, password)
			self.peer_repo.update_connection(username, host, port)
			self.send_response(conn, "OK", "Usuário registrado com sucesso.")
	
	def list_peers(self, conn):
		peer_list = []
		for peer in self.peer_repo.get_all_peers():
			status = "connected" if peer.connected else "disconnected"
			peer_list.append({
					"username": peer.username,
					"status": status,
					"room": self.get_room_of_peer(peer.username)
			})
		self.send_response(conn, "OK", peers=peer_list)
	
	def create_room(self, conn, data):
		room = data.get("room")
		user = data.get("username")
		
		if not room or not user:
			self.send_response(conn, "ERROR", "Parâmetros ausentes.")
			return
		
		peer_owner = self.peer_repo.get_peer(user)
		if not peer_owner:
			self.send_response(conn, "ERROR", f"Peer '{user}' não encontrado.")
			return
		
		if self.room_repo.create_room(room, peer_owner):
			self.send_response(conn, "OK", f"Sala '{room}' criada com sucesso.")
		else:
			self.send_response(conn, "ERROR", f"A sala '{room}' já existe.")
	
	def join_room(self, conn, data):
		room = data.get("room")
		username = data.get("username")
		
		if not room or not username:
			self.send_response(conn, "ERROR", "Parâmetros ausentes.")
			return
		
		peer = self.peer_repo.get_peer(username)
		if not peer:
			self.send_response(conn, "ERROR", "Peer não encontrado.")
			return
		
		if self.room_repo.join_room(room, peer):
			room_obj = self.room_repo.rooms.get(room)
			participants = [room_obj.peer_owner, room_obj.peer_one, room_obj.peer_two]
			
			other_peers = [
					p for p in participants if p and p.username != username
			]
			
			peer_info_list = [
					{
							"username": p.username,
							"address": p.address,
							"port": p.port
					} for p in other_peers
			]
			
			self.send_response(
					conn,
					"OK",
					f"Usuário '{username}' entrou na sala '{room}'.",
					room=room,
					peers=peer_info_list
			)
		else:
			self.send_response(conn, "ERROR", f"A sala '{room}' não existe ou está cheia.")
	
	def list_rooms(self, conn):
		room_names = self.room_repo.list_rooms()
		self.send_response(conn, "OK", rooms=room_names)
	
	def client(self, conn, addr):
		try:
			raw = conn.recv(1024).decode("utf-8")
			data = json.loads(raw)
			cmd = data.get("cmd")
			
			match cmd:
				case "LOGIN":
					self.login(conn, data)
				case "REGISTER":
					self.register(conn, data)
				case "LIST_PEERS":
					self.list_peers(conn)
				case "CREATE_ROOM":
					self.create_room(conn, data)
				case "JOIN_ROOM":
					self.join_room(conn, data)
				case "LIST_ROOMS":
					self.list_rooms(conn)
				case _:
					self.send_response(conn, "ERROR", "Comando não suportado.")
		except Exception as e:
			print(f"[ERRO] {addr}: {e}")
			self.send_response(conn, "ERROR", "Erro interno no servidor.")
		finally:
			conn.close()
	
	def get_room_of_peer(self, username):
		for name, room in self.room_repo.rooms.items():
			participants = [p.username for p in [room.peer_owner, room.peer_one, room.peer_two] if p]
			if username in participants:
				return name
		return None
	
	def remove_peer_from_all_rooms(self, username):
		for room in self.room_repo.rooms.values():
			changed = False
			if room.peer_owner and room.peer_owner.username == username:
				room.peer_owner = None
				changed = True
			if room.peer_one and room.peer_one.username == username:
				room.peer_one = None
				changed = True
			if room.peer_two and room.peer_two.username == username:
				room.peer_two = None
				changed = True
			if changed:
				self.room_repo.save_rooms()
	
	def ping_all_peers(self):
		while True:
			time.sleep(PING_INTERVAL)
			for peer in self.peer_repo.get_all_peers():
				if not peer.connected:
					continue
				try:
					with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
						s.settimeout(3)
						s.connect((peer.address, peer.port))
						s.send(json.dumps({"cmd": "PING"}).encode("utf-8"))
						response = s.recv(1024).decode("utf-8")
						data = json.loads(response)
						if data.get("cmd") == "PONG":
							if not peer.connected:
								print(f"[RECONECTADO] Peer {peer.username} voltou.")
							peer.connected = True
						else:
							raise Exception("Resposta inválida")
				except:
					if peer.connected:
						print(f"[DESCONECTADO] Peer {peer.username} caiu.")
					peer.connected = False
					self.remove_peer_from_all_rooms(peer.username)
			
			self.peer_repo.save_peers()
	
	def start(self):
		print(f"Tracker rodando em {self.host}:{self.port}")
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_socket.bind((self.host, self.port))
		server_socket.listen()
		
		threading.Thread(target=self.ping_all_peers, daemon=True).start()
		
		while True:
			conn, addr = server_socket.accept()
			thread = threading.Thread(target=self.client, args=(conn, addr))
			thread.start()


if __name__ == "__main__":
	tracker = TrackerService()
	tracker.start()
