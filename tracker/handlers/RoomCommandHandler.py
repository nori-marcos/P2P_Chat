from tracker.peer.peer_repository import PeerRepository
from tracker.room.room_repository import RoomRepository


class RoomCommandHandler:
	def __init__(self, room_repo: RoomRepository, peer_repo:PeerRepository, send_response_func):
		self.room_repo = room_repo
		self.peer_repo = peer_repo
		self.send_response = send_response_func
	
	def create_room(self, conn, data):
		room_name = data.get("room")
		username = data.get("username")
		
		if not room_name or not username:
			self.send_response(conn, "ERROR", "Parâmetros ausentes.")
			return
		
		peer_owner = self.peer_repo.get_peer(username)
		if not peer_owner:
			self.send_response(conn, "ERROR", f"Peer '{username}' não encontrado.")
			return
		
		if self.room_repo.create_room(room_name, peer_owner):
			self.send_response(conn, "OK", f"Sala '{room_name}' criada com sucesso.")
		else:
			self.send_response(conn, "ERROR", f"A sala '{room_name}' já existe.")
	
	def join_room(self, conn, data):
		room_name = data.get("room")
		username = data.get("username")
		
		if not room_name or not username:
			self.send_response(conn, "ERROR", "Parâmetros ausentes.")
			return
		
		peer = self.peer_repo.get_peer(username)
		if not peer:
			self.send_response(conn, "ERROR", "Peer não encontrado.")
			return
		
		if self.room_repo.join_room(room_name, peer):
			participants = self.room_repo.get_participants(room_name)
			
			other_peers_info = [
					{"username": p.username, "address": p.address, "port": p.port}
					for p in participants if p and p.username != username
			]
			
			self.send_response(
					conn, "OK", f"Usuário '{username}' entrou na sala '{room_name}'.",
					room=room_name, peers=other_peers_info
			)
		else:
			self.send_response(conn, "ERROR", f"A sala '{room_name}' não existe ou está cheia.")
	
	def list_rooms(self, conn, data):
		rooms = self.room_repo.load_rooms()
		room_as_dict = {
				name: room.to_dict() for name, room in rooms.items()
		}
		self.send_response(conn, "OK", rooms=room_as_dict)
