import json
import socket


def list_rooms():
	msg = {
			"cmd": "LIST_ROOMS"
	}
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(("localhost", 6060))
	s.send(json.dumps(msg).encode("utf-8"))
	response = s.recv(4096).decode("utf-8")
	data = json.loads(response)
	print("Salas disponíveis:", data["msg"])
	s.close()

if __name__ == "__main__":
	list_rooms()