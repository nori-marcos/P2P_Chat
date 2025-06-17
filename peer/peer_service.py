import threading

from peer_peer_communication import PeerPeerCommunication
from peer_tracker_communication import PeerTrackerCommunication


class PeerService:
	def __init__(self):
		self.peer_comm = PeerPeerCommunication()
		self.tracker_comm = PeerTrackerCommunication(
				self.peer_comm.actual_host,
				self.peer_comm.actual_port
		)
		self.username = None
		self.current_room = None
	
	def connect_to_room_peer(self, response):
		peers = response.get("peers", [])
		if peers:
			for peer in peers:
				if peer["username"] != self.username:
					self.peer_comm.connect_to_peer(peer)
		else:
			print("Você é o primeiro da sala. Aguardando outros peers...")
	
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
				self.tracker_comm.list_peers()
			
			elif choice == "2":
				self.tracker_comm.list_rooms()
			
			elif choice == "3":
				if self.username:
					room = self.tracker_comm.create_room(self.username)
					if room:
						self.current_room = room
						print("Sala criada. Você é o primeiro peer da sala.")
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
		print(f"Rodando em {self.peer_comm.actual_host}:{self.peer_comm.actual_port}")
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
