class Peer:
	def __init__(self, username: str, last_ping: dict = None, address: str = None, port: int = None,
	             connected: bool = False):
		self.username = username
		self.last_ping = last_ping if last_ping is not None else {}
		self.address = address
		self.port = None
		self.connected = connected
	
	def to_dict(self):
		return {
				"username": self.username,
				"last_ping": self.last_ping,
				"address": self.address,
				"port": self.port,
				"connected": self.connected
		}
	
	@staticmethod
	def from_dict(data: dict) -> 'Peer':
		return Peer(
				username=data.get("username"),
				last_ping=data.get("last_ping", {}),
				address=data.get("address"),
				port=data.get("port"),
				connected=data.get("connected", False)
		)
