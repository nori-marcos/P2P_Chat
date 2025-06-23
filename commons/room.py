from commons.peer import Peer


class Room:
	def __init__(self, name: str = None, peer_owner: Peer = None, peer_one: Peer = None,
	             peer_two: Peer = None):
		self.name = name
		self.peer_owner = peer_owner
		self.peer_one = peer_one
		self.peer_two = peer_two
	
	def to_dict(self) -> dict:
		return {
				"name": self.name,
				"peer_owner": self.peer_owner.to_dict() if self.peer_owner else None,
				"peer_one": self.peer_one.to_dict() if self.peer_one else None,
				"peer_two": self.peer_two.to_dict() if self.peer_two else None
		}
	
	@staticmethod
	def from_dict(data: dict) -> 'Room':
		return Room(
				name=data.get("name"),
				peer_owner=Peer.from_dict(data["peer_owner"]) if data.get("peer_owner") else None,
				peer_one=Peer.from_dict(data["peer_one"]) if data.get("peer_one") else None,
				peer_two=Peer.from_dict(data["peer_two"]) if data.get("peer_two") else None
		)
	
	def get_participants_usernames(self) -> list[str]:
		participants = []
		if self.peer_owner:
			participants.append(self.peer_owner.username)
		if self.peer_one:
			participants.append(self.peer_one.username)
		if self.peer_two:
			participants.append(self.peer_two.username)
		return participants
