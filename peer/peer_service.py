import threading
from datetime import datetime

from commons.room import Room
from peer.peer_peer_communication import PeerPeerCommunication
from peer.peer_tracker_communication import PeerTrackerCommunication


class PeerService:
	def __init__(self):
		self.print_lock = threading.Lock()
		self.current_room = None
		
		self.COLOR_RESET = "\033[0m"
		self.COLOR_SYSTEM = "\033[33m"
		self.available_colors = [
				"\033[36m", "\033[32m", "\033[33m",
				"\033[34m", "\033[35m", "\033[31m"
		]
		self.peer_colors = {}
		
		self.peer_comm = PeerPeerCommunication(message_callback=self.handle_p2p_message)
		self.tracker_comm = PeerTrackerCommunication(
				self.peer_comm.actual_address,
				self.peer_comm.actual_port,
				self
		)
		self.username = None
	
	@staticmethod
	def clear_screen():
		print("\033[H\033[J", end="")
	
	def safe_print(self, message, is_notification=False):
		with self.print_lock:
			if is_notification and self.current_room:
				prompt = f"Você ({self.username}): "
				print("\r" + " " * (len(prompt) + 70) + "\r", end="")
				print(message)
				print(prompt, end="", flush=True)
			else:
				print(message)
	
	def _get_peer_color(self, username: str) -> str:
		if username in self.peer_colors:
			return self.peer_colors[username]
		hash_val = hash(username)
		color_index = hash_val % len(self.available_colors)
		color = self.available_colors[color_index]
		self.peer_colors[username] = color
		return color
	
	def handle_p2p_message(self, command: str, sender_username: str, message_data: dict):
		timestamp = datetime.now().strftime('%H:%M:%S')
		user_color = self._get_peer_color(sender_username)
		colored_sender = f"{user_color}{sender_username}{self.COLOR_RESET}"
		
		if command == "MESSAGE":
			content = message_data.get('content')
			room_name = message_data.get('room')  # Check if a room name was included
			
			if room_name is not None:
				if self.current_room and self.current_room.name == room_name:
					self.safe_print(f"[{timestamp}] <{colored_sender}> {content}", is_notification=True)
			else:
				self.safe_print(
						f"[{timestamp}] {self.COLOR_SYSTEM}[PRIVADO de {colored_sender}]{self.COLOR_RESET} {content}",
						is_notification=True
				)
		
		elif command == "LEAVE":
			room_name = message_data.get('room')
			if self.current_room and self.current_room.name == room_name:
				self.safe_print(f"[{timestamp}] *** {colored_sender} saiu da sala.", is_notification=True)
	
	def update_current_room(self, room_data: dict):
		if not self.current_room or not room_data or self.current_room.name != room_data.get("name"):
			return
		
		timestamp = datetime.now().strftime('%H:%M:%S')
		old_peers = set(self.current_room.get_participants_usernames())
		self.current_room = Room.from_dict(room_data)
		new_peers = set(self.current_room.get_participants_usernames())
		
		added_peers = new_peers - old_peers
		if added_peers:
			self.safe_print(f"[{timestamp}] *** {', '.join(added_peers)} entrou na sala.", is_notification=True)
			all_peer_objects = self.current_room.list_participants()
			peers_to_connect = [p.to_dict() for p in all_peer_objects if p.username in added_peers]
			self.connect_to_room_peers(peers_to_connect)
		
		removed_peers = old_peers - new_peers
		if removed_peers:
			self.safe_print(f"[{timestamp}] *** {', '.join(removed_peers)} saiu da sala.", is_notification=True)
	
	def connect_to_room_peers(self, peers_info_list: list):
		if not peers_info_list:
			return
		
		self.safe_print("Conectando aos outros peers na sala...")
		for peer_info in peers_info_list:
			if peer_info and peer_info.get("username") != self.username:
				if peer_info.get("address") and peer_info.get("port"):
					self.peer_comm.connect_to_peer(peer_info, self.username)
				else:
					self.safe_print(
							f"{self.COLOR_SYSTEM}[AVISO] Informações para '{peer_info.get('username')}' incompletas.{self.COLOR_RESET}")
	
	def handle_private_chat(self, peer_username: str):
		self.clear_screen()
		
		user_color = self._get_peer_color(peer_username)
		colored_peer = f"{user_color}{peer_username}{self.COLOR_RESET}"
		
		header = (
				f"==================== CHAT PRIVADO COM: {colored_peer} ====================\n"
				f" Digite /sair para encerrar a conversa.\n"
				f"============================================================================"
		)
		self.safe_print(header)
		
		in_private_chat = True
		while in_private_chat and self.peer_comm.running:
			try:
				message = input(f"Você ({self.username}): ").strip()
				
				if message.lower() == "/sair":
					self.safe_print(f"Encerrando chat com {peer_username}...")
					self.peer_comm.disconnect_from_peer(peer_username)
					in_private_chat = False
					self.clear_screen()
					continue
				
				if message:
					timestamp = datetime.now().strftime('%H:%M:%S')
					print("\033[1A\033[K", end="")
					self.safe_print(f"[{timestamp}] <{self.username}> {message}")
					
					self.peer_comm.send_message(None, peer_username, self.username, message)
			
			except (KeyboardInterrupt, EOFError):
				self.safe_print(f"\nEncerrando chat com {peer_username}...")
				self.peer_comm.disconnect_from_peer(peer_username)
				in_private_chat = False
		
		self.safe_print("Retornando ao menu principal.")
	
	def handle_user_message_in_room(self):
		self.clear_screen()
		
		header = (
				f"==================== ROOM: {self.current_room.name} ====================\n"
				f" Online: {', '.join(self.current_room.get_participants_usernames())}\n"
				f" Digite /users, /help, /deletar_sala ou /sair\n"
				f"================================================================"
		)
		self.safe_print(header)
		
		while self.current_room and self.peer_comm.running:
			try:
				message = input(f"Você ({self.username}): ").strip()
				
				if message.lower() == '/sair':
					message = 'sair'
				elif message.lower() == '/users':
					participants = ", ".join(self.current_room.get_participants_usernames())
					self.safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] *** Usuários na sala: {participants}")
					continue
				elif message.lower() == '/deletar_sala':
					if self.current_room.peer_owner.username == self.username:
						participants_to_notify = self.current_room.get_participants_usernames()
						room_name_to_delete = self.current_room.name
						
						response = self.tracker_comm.delete_room(self.username, room_name_to_delete)
						
						if response and response.get("status") == "OK":
							self.safe_print(
									f"[{datetime.now().strftime('%H:%M:%S')}] *** Sala '{room_name_to_delete}' deletada.")
							
							self.current_room = None
							
							self.peer_comm.leave_room(participants_to_notify)
							
							return
						else:
							self.safe_print(
									f"[ERRO] Não foi possível deletar a sala: {response.get('msg', 'motivo desconhecido')}")
					else:
						self.safe_print("[ERRO] Apenas o proprietário da sala pode deletá-la.")
					continue
				elif message.lower() == '/help':
					self.safe_print("[INFO] Comandos: /users, /sair, /deletar_sala")
					continue
				
				if message.lower() == "sair":
					self.safe_print("Saindo da sala...")
					self.tracker_comm.leave_room(self.username, self.current_room.name)
					self.peer_comm.leave_room(self.current_room.get_participants_usernames())
					self.current_room = None
					self.clear_screen()
					return
				
				if message:
					timestamp = datetime.now().strftime('%H:%M:%S')
					
					print("\033[1A\033[K", end="")
					
					self.safe_print(f"[{timestamp}] <{self.username}> {message}")
					
					for to_username in self.current_room.get_participants_usernames():
						if to_username != self.username:
							self.peer_comm.send_message(self.current_room.name, to_username, self.username, message)
			
			except (KeyboardInterrupt, EOFError):
				self.safe_print("\nSaindo da sala...")
				self.tracker_comm.leave_room(self.username, self.current_room.name)
				self.peer_comm.leave_room(self.current_room.get_participants_usernames())
				self.current_room = None
				return
	
	def handle_user_input(self):
		while self.peer_comm.running:
			self.safe_print("\n--- MENU PRINCIPAL ---")
			print("1. Listar peers online")
			print("2. Listar salas disponíveis")
			print("3. Criar sala")
			print("4. Entrar em sala")
			print("5. Chat com um peer")
			print("0. Sair")
			
			choice = input("Escolha uma opção: ").strip()
			
			if choice == "1":
				response = self.tracker_comm.list_peers()
				if response and response.get("status") == "OK":
					peers_data = response.get("peers", {})
					print("\n--- Peers Online ---")
					if not peers_data:
						print("Nenhum peer online.")
					for username, peer_info in peers_data.items():
						print(f"- {username} (Online: {peer_info.get('connected')}, Sala: {peer_info.get('room')})")
				else:
					print(f"Erro ao listar peers: {response.get('msg')}")
			
			elif choice == "2":
				response = self.tracker_comm.list_rooms()
				if response and response.get("status") == "OK":
					rooms_data = response.get("rooms", {})
					print("\n--- Salas Disponíveis ---")
					if not rooms_data:
						print("Nenhuma sala disponível.")
					for name, room_info in rooms_data.items():
						usernames = [p['username'] for p in room_info.values() if p and isinstance(p, dict)]
						print(f"- {name} (Participantes: {len(usernames)}/3)")
				else:
					print(f"Erro ao listar salas: {response.get('msg')}")
			
			elif choice == "3":
				if self.username:
					room_name = input("Nome da sala: ")
					response = self.tracker_comm.create_room(self.username, room_name)
					print(f"{response.get('status')}: {response.get('msg')}")
				else:
					print("Você precisa estar logado para criar uma sala.")
			
			elif choice == "4":
				if self.username:
					room_name = input("Nome da sala: ")
					if not room_name:
						print("Nome da sala não pode ser vazio.")
						continue
					
					response = self.tracker_comm.join_room(self.username, room_name)
					
					if response and response.get("status") == "OK":
						room_data = response.get("room")
						if not room_data:
							print("[ERRO] Tracker não retornou dados da sala.")
							continue
						
						self.current_room = Room.from_dict(room_data)
						print(f"Entrou na sala: {self.current_room.name}")
						
						peers_to_connect = [p for p in room_data.values() if isinstance(p, dict) and p.get('username')]
						self.connect_to_room_peers(peers_to_connect)
						
						self.handle_user_message_in_room()
					else:
						error_msg = response.get('msg', 'motivo desconhecido')
						print(f"Erro ao entrar na sala: {error_msg}")
				else:
					print("Você precisa estar logado para entrar em uma sala.")
			
			elif choice == "5":
				if self.username:
					peer_username = input("Nome do peer para conversar: ").strip()
					if not peer_username:
						self.safe_print("Nome do peer não pode ser vazio.")
						continue
					
					if peer_username == self.username:
						self.safe_print("[AVISO] Você не pode conversar com você mesmo.")
						continue
					
					response = self.tracker_comm.list_peers()
					if response and response.get("status") == "OK":
						peers_data = response.get("peers", {})
						peer_info = peers_data.get(peer_username)
						
						if peer_info:
							if peer_info.get("connected") and peer_info.get("address") and peer_info.get("port"):
								is_connected = self.peer_comm.connect_to_peer(peer_info, self.username)
								if is_connected:
									self.handle_private_chat(peer_username)
								else:
									self.safe_print(f"Falha na conexão com {peer_username}.")
							else:
								self.safe_print(
									f"Peer '{peer_username}' está online, mas suas informações de conexão são inválidas.")
						else:
							self.safe_print(f"Peer '{peer_username}' não encontrado ou não está online.")
					else:
						self.safe_print(f"Erro ao listar peers: {response.get('msg')}")
				else:
					self.safe_print("Você precisa estar logado para se conectar a um peer.")
			
			elif choice == "0":
				print("Encerrando o peer...")
				self.tracker_comm.send_request({"cmd": "LOGOUT", "username": self.username})
				self.peer_comm.running = False
				break
			
			else:
				print("Opção inválida!")
	
	def handle_user_authentication(self):
		if not self.tracker_comm.connect():
			print("Não foi possível conectar ao servidor tracker. Encerrando.")
			return
		
		while self.peer_comm.running:
			print("\n--- AUTENTICAÇÃO ---")
			print("1. Login")
			print("2. Registrar")
			print("0. Sair")
			
			choice = input("Escolha uma opção: ").strip()
			
			if choice == "1":
				username = input("Nome de usuário: ")
				password = input("Senha: ")
				response = self.tracker_comm.login(username, password)
				if response and response.get("status") == "OK":
					self.username = username
					self.peer_comm.username = username
					print(response.get("msg"))
					self.handle_user_input()
					break
				else:
					print(f"Falha no login: {response.get('msg')}")
			
			elif choice == "2":
				username = input("Nome de usuário: ")
				password = input("Senha: ")
				response = self.tracker_comm.register(username, password)
				if response and response.get("status") == "OK":
					print(f"Registro bem-sucedido! Por favor, faça o login.")
				else:
					print(f"Falha no registro: {response.get('msg')}")
			
			elif choice == "0":
				return
			else:
				print("Opção inválida!")
	
	def start(self):
		threading.Thread(target=self.peer_comm.listen_for_peers, daemon=True).start()
		self.handle_user_authentication()
		
		print("\nFinalizando conexões...")
		self.peer_comm.close()
		self.tracker_comm.close()
		print("Peer encerrado.")


if __name__ == "__main__":
	peer = PeerService()
	peer.start()
