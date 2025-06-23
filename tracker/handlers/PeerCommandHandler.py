from tracker.peer.peer_repository import PeerRepository
from tracker.room.room_repository import RoomRepository


class PeerCommandHandler:
	def __init__(self, peer_repo: PeerRepository, room_repo: RoomRepository, send_response_func):
		self.peer_repo = peer_repo
		self.room_repo = room_repo
		self.send_response = send_response_func
	
	def list_peers(self, conn, data) -> None:
		online_peers_for_response = {}
		
		for username, peer_object in self.peer_repo.peers.items():
			
			if peer_object.connected:
				peer_data = peer_object.to_dict()
				room_name = self.room_repo.get_room_of_peer(username)
				peer_data['room'] = room_name if room_name else None
				online_peers_for_response[username] = peer_data
		
		self.send_response(conn, "OK", peers=online_peers_for_response)