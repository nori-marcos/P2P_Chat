import threading

from commons.room import Room
from peer.peer_peer_communication import PeerPeerCommunication
from peer.peer_tracker_communication import PeerTrackerCommunication


class PeerService:
	def __init__(self):
		self.current_room = None
		self.peer_comm = PeerPeerCommunication(message_callback=self.handle_p2p_message)
		self.tracker_comm = PeerTrackerCommunication(
				self.peer_comm.actual_address,
				self.peer_comm.actual_port,
				self  # Pass a reference to this PeerService instance
		)
		self.username = None
	
	def handle_p2p_message(self, command: str, sender_username: str, message_data: dict):
		if command == "MESSAGE":
			content = message_data.get('content')
			room_name = message_data.get('room')
			print(f"\r[MENSAGEM na sala {room_name} de {sender_username}] {content}")
			print(f"Você ({self.username}): ", end="", flush=True)
		
		elif command == "LEAVE":
			print(f"\r[INFO] {sender_username} saiu da sala.")
			print(f"Você ({self.username}): ", end="", flush=True)
	
	def update_current_room(self, room_data: dict):
		if self.current_room and room_data and self.current_room.name == room_data.get("name"):
			print(f"\n[INFO] A sala '{self.current_room.name}' foi atualizada pelo tracker.")
			
			old_peers = set(self.current_room.get_participants_usernames())
			self.current_room = Room.from_dict(room_data)
			new_peers = set(self.current_room.get_participants_usernames())
			
			added_peers = new_peers - old_peers
			if added_peers:
				print(f"[INFO] Novos peers entraram: {', '.join(added_peers)}")
				all_peer_objects = self.current_room.list_participants()
				peers_to_connect = [p.to_dict() for p in all_peer_objects if p.username in added_peers]
				self.connect_to_room_peers(peers_to_connect)
			
			removed_peers = old_peers - new_peers
			if removed_peers:
				print(f"[INFO] Peers saíram: {', '.join(removed_peers)}")
	
	def connect_to_room_peers(self, peers_info_list: list):
		if not peers_info_list:
			print("Você é o primeiro na sala. Aguardando outros peers...")
			return
		
		print("Conectando aos outros peers na sala...")
		for peer_info in peers_info_list:
			if peer_info and peer_info.get("username") != self.username:
				if peer_info.get("address") and peer_info.get("port"):
					self.peer_comm.connect_to_peer(peer_info, self.username)
				else:
					print(
							f"[AVISO] Informações de conexão para '{peer_info.get('username')}' incompletas. Não é possível conectar.")
	
	def handle_user_message_in_room(self):
		print(f"\n=== ROOM CHAT: {self.current_room.name} ===")
		while self.current_room and self.peer_comm.running:
			try:
				message = input(f"Você ({self.username}): ").strip()
				if message.lower() == "sair":
					print("Saindo da sala...")
					self.tracker_comm.leave_room(self.username, self.current_room.name)
					self.peer_comm.leave_room(self.current_room.get_participants_usernames())
					self.current_room = None
					return
				if message:
					for to_username in self.current_room.get_participants_usernames():
						if to_username != self.username:
							self.peer_comm.send_message(self.current_room.name, to_username, self.username, message)
			except (KeyboardInterrupt, EOFError):
				print("\nSaindo da sala...")
				self.tracker_comm.leave_room(self.username, self.current_room.name)
				self.peer_comm.leave_room(self.current_room.get_participants_usernames())
				self.current_room = None
				return
	
	def handle_user_input(self):
		while self.peer_comm.running:
			print("\n--- MENU PRINCIPAL ---")
			print("1. Listar peers online")
			print("2. Listar salas disponíveis")
			print("3. Criar sala")
			print("4. Entrar em sala")
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
