import json
import socket
import threading


class PeerPeerCommunication:
    def __init__(self, host="localhost", port=0):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        self.actual_host, self.actual_port = self.socket.getsockname()
        self.running = True
        self.connections = {}  # username -> socket

    def peer_connection(self, conn):
        try:
            data = conn.recv(1024).decode("utf-8")
            message = json.loads(data)
            cmd = message.get("cmd")

            if cmd == "PING":
                print("[TRACKER] Ping recebido.")
                conn.send(json.dumps({"cmd": "PONG"}).encode("utf-8"))

            elif cmd == "HELLO":
                origin = message.get("from")
                username = message.get("username")
                print(f"[PEER] Conexão recebida de {username} ({origin})")
                self.connections[username] = conn  # manter a conexão viva
                threading.Thread(target=self.receive_messages, args=(conn, username), daemon=True).start()

            elif cmd == "MESSAGE":
                sender = message.get("from")
                content = message.get("content")
                print(f"[MENSAGEM de {sender}] {content}")

            else:
                print(f"[PEER] Comando desconhecido: {cmd}")

        except Exception as e:
            print(f"[ERRO] na conexão com peer/tracker: {e}")
        # não fecha o conn aqui porque queremos manter conexão viva

    def listen_for_peers(self):
        while self.running:
            try:
                conn, addr = self.socket.accept()
                print(f"[ENTRADA] Conexão de: {addr}")
                threading.Thread(target=self.peer_connection, args=(conn,), daemon=True).start()
            except Exception as e:
                print(f"[ERRO] {e}")

    def connect_to_peer(self, peer_info):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((peer_info["address"], peer_info["port"]))

            hello_msg = {
                "cmd": "HELLO",
                "from": f"{self.actual_host}:{self.actual_port}",
                "username": peer_info["username"]
            }

            s.send(json.dumps(hello_msg).encode("utf-8"))
            self.connections[peer_info["username"]] = s

            threading.Thread(target=self.receive_messages, args=(s, peer_info["username"]), daemon=True).start()
            print(f"[CONECTADO] com {peer_info['username']} em {peer_info['address']}:{peer_info['port']}")

        except Exception as e:
            print(f"[FALHA] ao conectar com {peer_info['username']}: {e}")

    def receive_messages(self, conn, username):
        try:
            while self.running:
                data = conn.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode("utf-8"))
                if message.get("cmd") == "MESSAGE":
                    print(f"[MENSAGEM de {username}] {message.get('content')}")
        except Exception as e:
            print(f"[ERRO] ao receber mensagem de {username}: {e}")
        finally:
            conn.close()
            del self.connections[username]

    def send_message(self, to_username, content):
        conn = self.connections.get(to_username)
        if conn:
            try:
                conn.send(json.dumps({
                    "cmd": "MESSAGE",
                    "from": f"{self.actual_host}:{self.actual_port}",
                    "content": content
                }).encode("utf-8"))
            except Exception as e:
                print(f"[ERRO] ao enviar mensagem para {to_username}: {e}")
        else:
            print(f"[AVISO] Conexão com {to_username} não encontrada.")

    def close(self):
        self.running = False
        for conn in self.connections.values():
            try:
                conn.close()
            except:
                pass
        self.socket.close()
