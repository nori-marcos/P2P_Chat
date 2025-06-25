import hashlib
import json
import queue
import socket
import threading


class PeerTrackerCommunication:
	def __init__(self, peer_host: str, peer_port: int, peer_service):
		self.tracker_host = "localhost"
		self.tracker_port = 6060
		self.peer_host = peer_host
		self.peer_port = peer_port
		self.peer_service = peer_service
		
		self.socket = None
		self.running = True
		self.response_queue = queue.Queue()
		self.listener_thread = None
	
	def connect(self) -> bool:
		try:
			self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.socket.connect((self.tracker_host, self.tracker_port))
			self.listener_thread = threading.Thread(target=self.listen_for_tracker_messages, daemon=True)
			self.listener_thread.start()
			print("[INFO] Conectado ao tracker.")
			return True
		except ConnectionRefusedError:
			print("[ERRO] Conexão com o tracker foi recusada. O tracker está offline?")
			return False
		except Exception as e:
			print(f"[ERRO] Falha ao conectar com tracker: {e}")
			return False
	
	def listen_for_tracker_messages(self):
		while self.running:
			try:
				response_raw = self.socket.recv(4096)
				if not response_raw:
					print("[INFO] Conexão com o tracker foi perdida.")
					break
				
				response = json.loads(response_raw.decode("utf-8"))
				
				if response.get("status") == "ROOM_UPDATE":
					print(f"\n[ATUALIZAÇÃO DA SALA] {response.get('msg')}")
					self.peer_service.update_current_room(response.get("room"))
				else:
					self.response_queue.put(response)
			
			except ConnectionAbortedError:
				print("[INFO] Conexão com o tracker foi abortada.")
				break
			except Exception as e:
				print(f"[ERRO] na escuta do tracker: {e}")
				break
		self.running = False
	
	def send_request(self, message: dict) -> dict | None:
		if not self.socket or not self.running:
			print("[ERRO] Não conectado ao tracker.")
			return {"status": "ERROR", "msg": "Não conectado ao tracker."}
		try:
			self.socket.send(json.dumps(message).encode("utf-8"))
			return self.response_queue.get(timeout=5)
		except queue.Empty:
			print("[ERRO] Tracker não respondeu a tempo (timeout).")
			return {"status": "ERROR", "msg": "Tracker timeout."}
		except Exception as e:
			print(f"[ERRO] Falha ao enviar comando para o tracker: {e}")
			return {"status": "ERROR", "msg": str(e)}
	
	def close(self):
		print("[INFO] Desconectando do tracker...")
		self.running = False
		if self.socket:
			self.socket.close()
		if self.listener_thread:
			self.listener_thread.join()
	
	def login(self, username, password):
		hashed = hashlib.sha256(password.encode()).hexdigest()
		msg = {
				"cmd": "LOGIN",
				"username": username,
				"password": hashed,
				"address": self.peer_host,
				"port": self.peer_port
		}
		response = self.send_request(msg)
		return response
	
	def register(self, username, password):
		hashed = hashlib.sha256(password.encode()).hexdigest()
		msg = {
				"cmd": "REGISTER",
				"username": username,
				"password": hashed,
				"address": self.peer_host,
				"port": self.peer_port
		}
		response = self.send_request(msg)
		return response
	
	def list_peers(self):
		response = self.send_request({"cmd": "LIST_PEERS"})
		return response
	
	def list_rooms(self):
		response = self.send_request({"cmd": "LIST_ROOMS"})
		return response
	
	def create_room(self, username, room_name):
		response = self.send_request({
				"cmd": "CREATE_ROOM",
				"room": room_name,
				"username": username
		})
		return response
	
	def join_room(self, username, room_name):
		response = self.send_request({
				"cmd": "JOIN_ROOM",
				"room": room_name,
				"username": username
		})
		return response
	
	def leave_room(self, username, room_name):
		response = self.send_request({
				"cmd": "LEAVE_ROOM",
				"room": room_name,
				"username": username
		})
		return response
	
	def delete_room(self, username, room_name):
		response = self.send_request({
				"cmd": "DELETE_ROOM",
				"room": room_name,
				"username": username
		})
		return response
