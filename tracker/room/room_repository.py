import json
import os

from commons.peer import Peer
from commons.room import Room


class RoomRepository:
	def __init__(self, path=None):
		base_dir = os.path.dirname(__file__)
		self.path = path or os.path.join(base_dir, "rooms_db.json")
		self.rooms = self.load_rooms()
	
	def load_rooms(self) -> dict[str, Room]:
		if not os.path.exists(self.path):
			print(f"[INFO] Arquivo {self.path} não encontrado. Criando novo.")
			self._save_empty_rooms()
			return {}
		try:
			with open(self.path, "r") as f:
				data = json.load(f)
				return {name: Room.from_dict(room_dict) for name, room_dict in data.items()}
		except (json.JSONDecodeError, FileNotFoundError):
			print(f"[WARN] Arquivo {self.path} está vazio ou corrompido. Recriando base.")
			self._save_empty_rooms()
			return {}
	
	def _save_empty_rooms(self) -> None:
		with open(self.path, "w") as f:
			json.dump({}, f)
	
	def save_rooms(self) -> None:
		data = {name: Room.to_dict(room) for name, room in self.rooms.items()}
		with open(self.path, "w") as f:
			json.dump(data, f, indent=2)
	
	def create_room(self, room_name, peer_owner: Peer) -> bool:
		if not isinstance(peer_owner, Peer):
			raise ValueError("O proprietário da sala deve ser uma instância de Peer.")
		if room_name not in self.rooms:
			self.rooms[room_name] = Room(name=room_name, peer_owner=peer_owner)
			self.save_rooms()
			return True
		return False
	
	def join_room(self, room_name, peer: Peer) -> bool:
		room = self.rooms.get(room_name)
		
		if not room:
			return False
		
		if peer.username in room.get_participants_usernames():
			return True
		
		if not room.peer_one:
			room.peer_one = peer
		elif not room.peer_two:
			room.peer_two = peer
		else:
			return False
		
		self.save_rooms()
		return True
	
	def leave_room(self, room_name, peer: Peer) -> bool:
		room = self.rooms.get(room_name)
		if not room:
			return False
		
		if room.peer_owner and room.peer_owner.username == peer.username:
			del self.rooms[room_name]
		elif room.peer_one and room.peer_one.username == peer.username:
			room.peer_one = None
		elif room.peer_two and room.peer_two.username == peer.username:
			room.peer_two = None
		else:
			return False
		
		self.save_rooms()
		return True
	
	def list_rooms(self):
		return list(self.rooms.keys())
	
	def get_room_of_peer(self, username):
		for name, room in self.rooms.items():
			participants = room.get_participants_usernames()
			if username in participants:
				return name
		return None
	
	def get_room(self, room_name) -> Room:
		return self.rooms.get(room_name)
