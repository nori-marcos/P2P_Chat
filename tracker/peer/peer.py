class Peer:
    def __init__(self, username: str):
        self.username = username
        self.last_ping = {}
        self.address = None
        self.port = None
        self.connected = False

    def to_dict(self):
        return {
            "username": self.username,
            "last_ping": self.last_ping,
            "address": self.address,
            "port": self.port,
            "connected": self.connected
        }

    @staticmethod
    def from_dict(data):
        peer = Peer(data["username"])
        peer.last_ping = data.get("last_ping", {})
        peer.address = data.get("address")
        peer.port = data.get("port")
        peer.connected = data.get("connected", False)
        return peer
