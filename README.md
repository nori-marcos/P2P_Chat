---
pdf_options:
  format: A4
  margin: 100px 40px
  printBackground: true
  displayHeaderFooter: true
  headerTemplate: |
    <div style="width: 100%; padding-right: 40px; box-sizing: border-box; font-family: sans-serif; font-size: 10px; text-align: right;">
    </div>
  footerTemplate: |
    <style>
      section {
        font-family: sans-serif;
        font-size: 10px;
        width: 100%;
        text-align: center;
      }
    </style>
    <section>
      Página <span class="pageNumber"></span> de <span class="totalPages"></span>
    </section>
highlightTheme: monokai
---

**Universidade de Brasília (UnB)**  
Departamento de Ciência da Computação  
Disciplina: Redes de Computadores <br>
**Alunos:** Marcos Noriyuki Miyata – 18/0126890 e Valeria Alexandra Guevara Parra – 24/2039775  
**Professor:** JACIR LUIZ BORDIM  
**Semestre:** 1º/2025

<div align="center">
<h1>Trabalho Prático: Implementação de um Chat P2P</h1>
</div>

[**Link do repositório no github**](https://github.com/nori-marcos/P2P_Chat.git)

**Índice**

> - [P2P Chat](#p2p-chat)
    > - [1. Tracker](#1-tracker)
> - [2. Peer](#2-peer)

# P2P Chat

## 1. Tracker

O tracker é um servidor que mantém uma lista de peers conectados e suas respectivas portas. Ele permite que os peers se
registrem e obtenham informações sobre outros peers disponíveis na rede.

Para iniciar uma instância do tracker, são necessários os parâmetros de host, porta e o caminho para o banco de dados de
usuários. O users_db é um arquivo JSON que armazena o nome e a senha criptografada dos usuários registrados.

```python
class TrackerServer:
	def __init__(self, host='localhost', port=6060, users_db='users_db.json'):
		self.host = host
		self.port = port
		self.users_db = users_db
		self.users = self.load_users()
		self.peers = {}
		self.login_history = {}
		self.last_ping = {}
		self.rooms = {}
```

Os atributos principais do tracker incluem:

- `host`: Endereço IP do tracker.
- `port`: Porta na qual o tracker escuta conexões.
- `users_db`: Caminho para o arquivo JSON que armazena os usuários registrados.
- `users`: Dicionário que carrega os usuários do banco de dados.
- `peers`: Dicionário que mapeia os peers conectados e seus respectivos endereços IP e portas.
- `login_history`: Dicionário que registra o histórico de login dos usuários.
- `last_ping`: Dicionário que armazena o último ping recebido de cada peer para saber se estão ativos.
- `rooms`: Dicionário que mapeia salas de chat e seus respectivos participantes.

Em relação aos principais métodos:

- `load_users()`: Carrega os usuários do banco de dados salvo no arquivo `users_db.json`.
- `save_users()`: Salva os usuários no banco de dados no arquivo `users_db.json`.
- `handle_login()`: Autentica um usuário recebendo nome e senha, e registra seu peer. Depois da autenticação, o peer é
  adicionado à lista de peers conectados.
- `handle_register()`: Registra um novo usuário com nome e senha, verifica se o nome de usuário já existe.
- `handle_list_peers()`: Retorna a lista de peers conectados, mostrando o nome, o seu último login e seus status online
  ou offline de acordo com o seu último ping (se foi recebido nos últimos 30 segundos).
- `handle_ping()`: Atualiza o timestamp do último ping de um peer.
- `handle_create_room()`: Cria uma nova sala de chat, verifica se o nome da sala já existe e adiciona o peer
  como participante.
- `handle_list_rooms()`: Retorna a lista de salas de chat disponíveis, mostrando o nome da sala e os participantes.
- `handle_join_room()`: Adiciona um peer a uma sala de chat existente.
- `handle_client()`: Método principal que lida com as requisições dos peers: LOGIN, REGISTER, LIST_PEERS, PING,
  CREATE_ROOM, LIST_ROOMS, JOIN_ROOM. Ele recebe as requisições dos peers e chama o método apropriado para tratá-las.
- `start()`: Inicia o servidor tracker, escutando conexões na porta especificada e aguardando requisições dos peers.

### Captura de tela
#### Registro de usuário
Caso em que usuário já existe:
![img.png](captions/wireshark-registration.png)

Comunicação entre o tracker e o peer:
![img.png](captions/wireshark-registration-stream.png)

Logs do tracker e do peer:
![img.png](captions/terminal-tracker-peer-logs.png)

Caso de sucesso:
![img.png](captions/terminal-peer-registration-log.png)

#### Autenticação de usuário
Teste de autenticação com válido e inválido:
![img.png](captions/terminal-peer-login-log.png)

#### Registro de informação no arquivo JSON
![img.png](captions/db-json.png)

## 2. Peer