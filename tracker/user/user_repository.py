import json
import os

from commons.user import User


class UserRepository:
	def __init__(self, path=None):
		base_dir = os.path.dirname(__file__)
		self.path = path or os.path.join(base_dir, "users_db.json")
		self.users = self.load_users()
	
	def load_users(self):
		if not os.path.exists(self.path):
			with open(self.path, "w") as f:
				json.dump({}, f)
			return {}
		
		try:
			with open(self.path, "r") as f:
				raw_users = json.load(f)
				return {username: User(username, password) for username, password in raw_users.items()}
		except (json.JSONDecodeError, FileNotFoundError, ValueError):
			print(f"[WARN] Arquivo {self.path} vazio ou corrompido. Recriando base.")
			with open(self.path, "w") as f:
				json.dump({}, f)
			return {}
	
	def save_users(self):
		with open(self.path, "w") as f:
			raw_users = {name: user.password for name, user in self.users.items()}
			json.dump(raw_users, f, indent=2)
	
	def create_user(self, username, password):
		if username in self.users:
			return False
		self.users[username] = User(username, password)
		self.save_users()
		return True
	
	def validate_user(self, username, password):
		user = self.users.get(username)
		return user is not None and user.password == password
	
	def user_exists(self, username):
		return username in self.users
	
	def get_user(self, username):
		return self.users.get(username)
