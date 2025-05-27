import socket
import json
import hashlib

"""
Testa o login de um usuário no tracker.
"""
def login(user, password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    msg = {
        "cmd": "LOGIN",
        "user": user,
        "password": hashed
    }
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 6060))
    s.send(json.dumps(msg).encode("utf-8"))
    response = s.recv(1024).decode("utf-8")
    data = json.loads(response)
    print(data["msg"])

if __name__ == "__main__":
    peers = [{"user": "marcos", "password": "senha_segura"}, {"user": "joao", "password": "senha_fraca"}]
    for peer in peers:
        print(f"Testando login para {peer['user']}...")
        login(peer["user"], peer["password"])
        print("-" * 30)
