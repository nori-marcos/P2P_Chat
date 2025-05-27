import socket
import json

"""
Testa a listagem de peers conectados ao tracker.
"""
def list_peers():
    msg = {
        "cmd": "LIST_PEERS"
    }

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 6060))
    s.send(json.dumps(msg).encode("utf-8"))

    response = s.recv(4096).decode("utf-8")
    data = json.loads(response)

    if data["status"] == "OK":
        if "peers" in data:
            print("Peers conectados:")
            for peer in data["peers"]:
                print(f"- {peer['user']} (Último login: {peer['last_login']}, Status: {peer['status']})")
        else:
            print(f"{data.get('msg', 'Nenhum peer conectado.')}")
    else:
        print(f"Erro: {data.get('msg', 'Resposta inválida do tracker.')}")

    s.close()

if __name__ == "__main__":
    list_peers()
