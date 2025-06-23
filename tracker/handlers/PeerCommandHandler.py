from tracker.peer.peer_repository import PeerRepository


class PeerCommandHandler:
	def __init__(self, peer_repo: PeerRepository, send_response_func):
		self.peer_repo = peer_repo
		self.send_response = send_response_func
	
	def list_peers(self, conn, data) -> None:
		peers = self.peer_repo.load_peers()
		
		online_peers = {}
		for username, peer in peers.items():
			if peer.connected:
				online_peers[username] = peer
		
		online_peers_as_dict = {
				username: peer.to_dict() for username, peer in online_peers.items()
		}
		
		self.send_response(conn, "OK", peers=online_peers_as_dict)
