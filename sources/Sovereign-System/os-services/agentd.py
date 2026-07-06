import socket, json, logging
from threading import Thread
logging.basicConfig(level=logging.INFO)
class AgentDaemon:
    def __init__(self, host='0.0.0.0', port=8443):
        self.host = host
        self.port = port
    def start(self):
        s = socket.socket()
        s.bind((self.host, self.port))
        s.listen(5)
        logging.info(f'Listening on {self.host}:{self.port}')
        while True:
            c, a = s.accept()
            Thread(target=self.handle, args=(c, a)).start()
    def handle(self, c, a):
        data = c.recv(4096).decode()
        msg = json.loads(data)
        c.send(json.dumps({'status': 'ok', 'cmd': msg.get('command')}).encode())
        c.close()
if __name__ == '__main__':
    AgentDaemon().start()
