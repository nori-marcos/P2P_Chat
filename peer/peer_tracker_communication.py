import hashlib
import json
import socket


class PeerTrackerCommunication:
	def __init__(self, host, port):
		self.actual_host = host
		self.actual_port = port
	
	def send_tracker_message(self, message):
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.connect(("localhost", 6060))
				s.send(json.dumps(message).encode("utf-8"))
				response = s.recv(4096).decode("utf-8")  # aumentei o buffer
				return json.loads(response)
		except Exception as e:
			print(f"[ERRO] Falha ao conectar com tracker: {e}")
			return {"status": "ERROR", "msg": str(e)}
	
	def login(self, username, password):
		hashed = hashlib.sha256(password.encode()).hexdigest()
		msg = {
				"cmd": "LOGIN",
				"username": username,
				"password": hashed,
				"host": self.actual_host,
				"port": self.actual_port
		}
		response = self.send_tracker_message(msg)
		print(f"{response.get('status')}: {response.get('msg')}")
		return response
	
	def register(self, username, password):
		hashed = hashlib.sha256(password.encode()).hexdigest()
		msg = {
				"cmd": "REGISTER",
				"username": username,
				"password": hashed,
				"host": self.actual_host,
				"port": self.actual_port
		}
		response = self.send_tracker_message(msg)
		print(f"{response.get('status')}: {response.get('msg')}")
		return response
	
	def list_peers(self):
		response = self.send_tracker_message({"cmd": "LIST_PEERS"})
		if response.get("status") == "OK":
			print("Peers conectados:")
			for peer in response.get("peers", []):
				print(
					f"- {peer['username']} (Status: {peer.get('status', 'desconhecido')}, Sala: {peer.get('room', 'nenhuma')})")
		else:
			print(f"Erro: {response.get('msg', 'Nenhum peer conectado.')}")
	
	def list_rooms(self):
		response = self.send_tracker_message({"cmd": "LIST_ROOMS"})
		if response.get("status") == "OK":
			print("Salas disponíveis:")
			for room in response.get("msg", []):
				print(f"- {room}")
		else:
			print(f"Erro: {response.get('msg', 'Nenhuma sala encontrada.')}")
	
	def create_room(self, username):
		room_name = input("Nome da sala: ")
		response = self.send_tracker_message({
				"cmd": "CREATE_ROOM",
				"room": room_name,
				"username": username
		})
		print(f"{response.get('status')}: {response.get('msg')}")
		return room_name if response.get("status") == "OK" else None
	
	def join_room(self, username):
		room_name = input("Nome da sala: ")
		response = self.send_tracker_message({
				"cmd": "JOIN_ROOM",
				"room": room_name,
				"username": username
		})
		print(f"{response.get('status')}: {response.get('msg')}")
		return response if response.get("status") == "OK" else None
