from tracker.peer.peer_repository import PeerRepository
from tracker.room.room_repository import RoomRepository


class RoomCommandHandler:
	def __init__(self, room_repo: RoomRepository, peer_repo: PeerRepository, send_response_func, active_connections):
		self.room_repo = room_repo
		self.peer_repo = peer_repo
		self.send_response = send_response_func
		self.active_connections = active_connections
	
	def _notify_participants(self, room_name: str, room_dict: dict, participants_to_notify: list):
		for participant in participants_to_notify:
			participant_socket = self.active_connections.get(participant.username)
			if participant_socket:
				print(f"[NOTIFICANDO] Enviando ROOM_UPDATE para {participant.username}")
				self.send_response(
						participant_socket, "ROOM_UPDATE",
						msg=f"A configuração da sala '{room_name}' foi atualizada.",
						room=room_dict
				)
	
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
		
		room = self.room_repo.get_room(room_name)
		if not room:
			self.send_response(conn, "ERROR", f"A sala '{room_name}' não existe.")
			return
		
		existing_participants = room.list_participants()
		
		if self.room_repo.join_room(room_name, peer):
			updated_room = self.room_repo.get_room(room_name)
			updated_room_dict = updated_room.to_dict()
			
			self._notify_participants(room_name, updated_room_dict, existing_participants)
			
			self.send_response(
					conn, "OK", f"Usuário '{username}' entrou na sala '{room_name}'.",
					room=updated_room_dict
			)
		else:
			self.send_response(conn, "ERROR", f"A sala '{room_name}' não existe ou está cheia.")
	
	def leave_room(self, conn, data):
		room_name = data.get("room")
		username = data.get("username")
		if not room_name or not username:
			self.send_response(conn, "ERROR", "Parâmetros ausentes.")
			return
		
		peer = self.peer_repo.get_peer(username)
		if not peer:
			self.send_response(conn, "ERROR", "Peer não encontrado.")
			return
		
		if self.room_repo.leave_room(room_name, peer):
			updated_room = self.room_repo.get_room(room_name)
			updated_room_dict = updated_room.to_dict() if updated_room else None
			
			if updated_room:
				self._notify_participants(room_name, updated_room_dict, updated_room.list_participants())
			
			self.send_response(conn, "OK", f"Usuário '{username}' saiu da sala '{room_name}'.")
		else:
			self.send_response(conn, "ERROR", f"Usuário '{username}' não está na sala '{room_name}'.")
	
	def list_rooms(self, conn, data):
		rooms = self.room_repo.load_rooms()
		room_as_dict = {
				name: room.to_dict() for name, room in rooms.items()
		}
		self.send_response(conn, "OK", rooms=room_as_dict)
	
	def delete_room(self, conn, data):
		room_name = data.get("room")
		username = data.get("username")
		if not room_name:
			self.send_response(conn, "ERROR", "Parâmetro 'room' ausente.")
			return
		
		if self.room_repo.delete_room(room_name, username):
			self.send_response(conn, "OK", f"Sala '{room_name}' deletada com sucesso.")
		else:
			self.send_response(conn, "ERROR", f"A sala '{room_name}' não existe ou não pode ser deletada.")
