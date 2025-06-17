import json
import os

from tracker.peer.peer import Peer
from tracker.room.room import Room


class RoomRepository:
    def __init__(self, path=None):
        base_dir = os.path.dirname(__file__)
        self.path = path or os.path.join(base_dir, "rooms_db.json")
        self.rooms = self.load_rooms()

    @classmethod
    def room_to_dict(cls, room: Room):
        return {
            "name": room.name,
            "peer_owner": Peer.to_dict(room.peer_owner) if room.peer_owner else None,
            "peer_one": Peer.to_dict(room.peer_one) if room.peer_one else None,
            "peer_two": Peer.to_dict(room.peer_two) if room.peer_two else None,
        }

    @classmethod
    def room_from_dict(cls, room_dict):
        return Room(
            name=room_dict.get("name"),
            peer_owner=Peer.from_dict(room_dict["peer_owner"]) if room_dict.get("peer_owner") else None,
            peer_one=Peer.from_dict(room_dict["peer_one"]) if room_dict.get("peer_one") else None,
            peer_two=Peer.from_dict(room_dict["peer_two"]) if room_dict.get("peer_two") else None,
        )

    def load_rooms(self):
        if not os.path.exists(self.path):
            print(f"[INFO] Arquivo {self.path} não encontrado. Criando novo.")
            self._save_empty_rooms()
            return {}

        try:
            with open(self.path, "r") as f:
                data = json.load(f)
                return {name: self.room_from_dict(room_dict) for name, room_dict in data.items()}
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"[WARN] Arquivo {self.path} está vazio ou corrompido. Recriando base.")
            self._save_empty_rooms()
            return {}

    def _save_empty_rooms(self):
        with open(self.path, "w") as f:
            json.dump({}, f)

    def save_rooms(self):
        data = {name: self.room_to_dict(room) for name, room in self.rooms.items()}
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def create_room(self, room_name, peer_owner: Peer):
        if not isinstance(peer_owner, Peer):
            raise ValueError("O proprietário da sala deve ser uma instância de Peer.")

        if room_name not in self.rooms:
            self.rooms[room_name] = Room(name=room_name, peer_owner=peer_owner)
            self.save_rooms()
            return True
        return False

    def join_room(self, room_name, peer: Peer):
        room = self.rooms.get(room_name)
        if not room:
            return False

        if not room.peer_one:
            room.peer_one = peer
        elif not room.peer_two:
            room.peer_two = peer
        else:
            return False

        self.save_rooms()
        return True

    def list_rooms(self):
        return list(self.rooms.keys())

    def get_participants(self, room_name):
        room = self.rooms.get(room_name)
        if not room:
            return []
        return [p for p in [room.peer_owner, room.peer_one, room.peer_two] if p]
