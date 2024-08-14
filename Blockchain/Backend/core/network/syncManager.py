from Blockchain.Backend.core.network.connection import Node

class syncManager:
    # def __init__(self, host, port, newBlockAvailable = None, secondryChain = None, Mempool = None):
    def __init__(self, host, port):
        self.host = host
        self.port = port 

    def spinUpTheServer(self):
        self.server = Node(self.host, self.port)
        self.server.startServer()
        print("SERVER STARTED")
        print(f"[LISTENING] at {self.host}:{self.port}")
        """
        while True:
            self.conn, self.addr = self.server.acceptConnection()
            handleConn = Thread(target = self.handleConnection)
            handleConn.start()
        """