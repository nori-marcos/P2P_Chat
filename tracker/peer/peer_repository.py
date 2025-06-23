import json
import os

from commons.peer import Peer


class PeerRepository:
    def __init__(self, path=None):
        base_dir = os.path.dirname(__file__)
        self.path = path or os.path.join(base_dir, "peers_db.json")
        self.peers = self.load_peers()

    def load_peers(self) -> dict[str, Peer]:
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({}, f)
            return {}

        try:
            with open(self.path, "r") as f:
                data = json.load(f)
                return {
                    username: Peer.from_dict(peer_data)
                    for username, peer_data in data.items()
                }
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"[WARN] Arquivo {self.path} vazio ou corrompido. Recriando base.")
            with open(self.path, "w") as f:
                json.dump({}, f)
            return {}

    def save_peers(self):
        data = {
            username: peer.to_dict()
            for username, peer in self.peers.items()
        }
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)

    def add_peer(self, peer: Peer):
        if not isinstance(peer, Peer):
            raise ValueError("O objeto deve ser uma instância de Peer")
        self.peers[peer.username] = peer
        self.save_peers()

    def remove_peer(self, username: str):
        if username in self.peers:
            del self.peers[username]
            self.save_peers()

    def get_peer(self, username: str):
        return self.peers.get(username)

    def get_all_peers(self):
        return list(self.peers.values())

    def is_connected(self, username: str):
        peer = self.get_peer(username)
        return peer.connected if peer else False

    def update_connection(self, username: str, address: str, port: int):
        peer = self.get_peer(username)
        if not peer:
            peer = Peer(username)
        peer.address = address
        peer.port = port
        peer.connected = True
        self.peers[username] = peer
        self.save_peers()
