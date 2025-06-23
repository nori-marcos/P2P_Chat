import json
import socket
import threading
import time

from tracker.handlers.PeerCommandHandler import PeerCommandHandler
from tracker.handlers.RoomCommandHandler import RoomCommandHandler
from tracker.handlers.UserCommandHandler import UserCommandHandler
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
		
		self.user_handler = UserCommandHandler(self.user_repo, self.peer_repo, self.send_response)
		self.room_handler = RoomCommandHandler(self.room_repo, self.peer_repo, self.send_response)
		self.peer_handler = PeerCommandHandler(self.peer_repo, self.send_response)
	
	def send_response(self, conn, status, msg=None, **extra_fields):
		response = {"status": status}
		if msg is not None:
			response["msg"] = msg
		response.update(extra_fields)
		try:
			conn.send(json.dumps(response).encode("utf-8"))
		except (ConnectionResetError, BrokenPipeError) as e:
			print(f"[AVISO] Não foi possível enviar resposta: {e}")
	
	def handle_client_request(self, conn, addr):
		try:
			raw_data = conn.recv(1024).decode("utf-8")
			if not raw_data:
				return
			data = json.loads(raw_data)
			cmd = data.get("cmd")
			
			if cmd in ["LOGIN", "REGISTER"]:
				handler_method = getattr(self.user_handler, cmd.lower())
				handler_method(conn, data)
			elif cmd in ["CREATE_ROOM", "JOIN_ROOM", "LIST_ROOMS"]:
				handler_method = getattr(self.room_handler, cmd.lower())
				handler_method(conn, data)
			elif cmd == "LIST_PEERS":
				self.peer_handler.list_peers(conn, data)
			else:
				self.send_response(conn, "ERROR", "Comando não suportado.")
		
		except json.JSONDecodeError:
			print(f"[ERRO] {addr}: Dados inválidos recebidos.")
			self.send_response(conn, "ERROR", "JSON mal-formatado.")
		except Exception as e:
			print(f"[ERRO] {addr}: {e}")
			self.send_response(conn, "ERROR", "Erro interno no servidor.")
		finally:
			conn.close()
	
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
			for peer in list(self.peer_repo.peers.values()):
				if not peer.connected or not peer.address or not peer.port:
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
			thread = threading.Thread(target=self.handle_client_request, args=(conn, addr))
			thread.start()


if __name__ == "__main__":
	tracker = TrackerService()
	tracker.start()
