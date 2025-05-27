import socket
import json
import hashlib

"""
Testa o registro de um usuário no tracker.
"""
def register(user, password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    msg = {
        "cmd": "REGISTER",
        "user": user,
        "password": hashed
    }
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 6060))
    s.send(json.dumps(msg).encode("utf-8"))
    response = s.recv(1024).decode("utf-8")
    print(json.loads(response)["msg"])
    s.close()

if __name__ == "__main__":
    register("marcos", "senha_segura")