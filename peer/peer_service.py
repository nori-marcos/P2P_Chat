import threading

from commons.peer import Peer
from commons.room import Room
from peer.peer_peer_communication import PeerPeerCommunication
from peer.peer_tracker_communication import PeerTrackerCommunication


class PeerService:
	def __init__(self):
		self.current_room = None
		self.peer_comm = PeerPeerCommunication()
		self.tracker_comm = PeerTrackerCommunication(
				self.peer_comm.actual_address,
				self.peer_comm.actual_port
		)
		self.username = None
		self.online_peers = {}
		self.available_rooms = {}
	
	def handle_user_message_in_room(self):
		print(self.current_room)
		while self.current_room and self.peer_comm.running:
			try:
				message = input("Digite sua mensagem (ou 'sair' para sair da sala): ").strip()
				if message.lower() == "sair":
					print("Saindo da sala...")
					self.peer_comm.leave_room(self.current_room.get_participants_usernames())
					self.current_room = None
					return
				if message:
					for to_username in self.current_room.get_participants_usernames():
						if to_username != self.username:
							self.peer_comm.send_message(self.current_room.name, to_username, self.username, message)
					print(f"Mensagem enviada para a sala {self.current_room.name}.")
			except KeyboardInterrupt:
				print("\nSaindo da sala...")
				self.current_room = None
				return
	
	def handle_user_input(self):
		while self.peer_comm.running:
			if self.current_room:
				print(f"\n[Você está na sala: {self.current_room}]")
			else:
				print("\n[Você ainda não entrou em uma sala]")
			
			print("Opções do peer:")
			print("1. Listar peers conectados")
			print("2. Listar salas disponíveis")
			print("3. Criar sala")
			print("4. Entrar em sala")
			print("5. Enviar mensagem para peer")
			print("0. Sair")
			
			choice = input("Escolha uma opção: ").strip()
			
			if choice == "1":
				self.online_peers = self.tracker_comm.list_peers()
			elif choice == "2":
				self.available_rooms = self.tracker_comm.list_rooms()
			elif choice == "3":
				if self.username:
					room_name = self.tracker_comm.create_room(self.username)
					if room_name:
						self.current_room = Room(name=room_name, peer_owner=Peer(username=self.username,
						                                                         address=self.peer_comm.actual_address,
						                                                         port=self.peer_comm.actual_port,
						                                                         connected=True))
						print("Sala criada. Você é o primeiro peer da sala.")
						self.handle_user_message_in_room()
				else:
					print("Você precisa estar logado para criar uma sala.")
			
			elif choice == "4":
				if self.username:
					response = self.tracker_comm.join_room(self.username)
					if response and response["status"] == "OK":
						self.current_room = response.get("room")
						print(f"Entrou na sala: {self.current_room}")
						self.connect_to_room_peer(response)
				else:
					print("Você precisa estar logado para entrar em uma sala.")
			
			elif choice == "5":
				to_username = input("Nome do peer destinatário: ")
				content = input("Mensagem: ")
				self.peer_comm.send_message(to_username, content)
			
			elif choice == "0":
				print("Encerrando o peer...")
				self.peer_comm.close()
				break
			
			else:
				print("Opção inválida!")
	
	def handle_user_authentication(self):
		print("=== PEER SERVICE ===")
		print(f"Rodando em {self.peer_comm.actual_address}:{self.peer_comm.actual_port}")
		while self.peer_comm.running:
			print("\nOpções de autenticação:")
			print("1. Login")
			print("2. Register")
			print("0. Sair")
			
			choice = input("Escolha uma opção: ").strip()
			
			if choice == "1":
				username = input("Nome de usuário: ")
				password = input("Senha: ")
				response = self.tracker_comm.login(username, password)
				if response["status"] == "OK":
					self.username = username
					self.peer_comm.username = username
					self.handle_user_input()
			
			elif choice == "2":
				username = input("Nome de usuário: ")
				password = input("Senha: ")
				response = self.tracker_comm.register(username, password)
				if response["status"] == "OK":
					self.username = username
					self.peer_comm.username = username
					self.handle_user_input()
			
			elif choice == "0":
				print("Encerrando o peer...")
				self.peer_comm.close()
				break
			
			else:
				print("Opção inválida!")
	
	def start(self):
		threading.Thread(target=self.peer_comm.listen_for_peers, daemon=True).start()
		self.handle_user_authentication()


if __name__ == "__main__":
	peer = PeerService()
	peer.start()
