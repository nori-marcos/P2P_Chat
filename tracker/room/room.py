from tracker.peer.peer import Peer


class Room:
	def __init__(self, name: str = None, peer_owner: Peer = None, peer_one: Peer = None,
	             peer_two: Peer = None):
		self.name = name
		self.peer_owner = peer_owner
		self.peer_one = peer_one
		self.peer_two = peer_two
