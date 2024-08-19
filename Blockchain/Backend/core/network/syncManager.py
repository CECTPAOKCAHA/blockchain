from Blockchain.Backend.core.network.connection import Node
from Blockchain.Backend.core.database.database import BlockchainDB
from Blockchain.Backend.core.network.network import requestBlock
from threading import Thread

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
        
        while True:
            self.conn, self.addr = self.server.acceptConnection()
            handleConn = Thread(target = self.handleConnection)
            handleConn.start()

    def handleConnection(self):
        envelope = self.server.read()
        try:
            """
            if len(str(self.addr[1])) == 4:
                self.addNode()
            
            if envelope.command == b'Tx':
                Transaction = Tx.parse(envelope.stream())
                Transaction.TxId = Transaction.id()
                self.Mempool[Transaction.TxId] = Transaction

            if envelope.command == b'block':
                blockObj = Block.parse(envelope.stream())
                BlockHeaderObj = BlockHeader(blockObj.BlockHeader.version,
                            blockObj.BlockHeader.prevBlockHash, 
                            blockObj.BlockHeader.merkleRoot, 
                            blockObj.BlockHeader.timestamp,
                            blockObj.BlockHeader.bits,
                            blockObj.BlockHeader.nonce)
                
                self.newBlockAvailable[BlockHeaderObj.generateBlockHash()] = blockObj
                print(f"New Block Received : {blockObj.Height}")

                """

            if envelope.command == requestBlock.command:
                start_block, end_block = requestBlock.parse(envelope.stream())
                #self.sendBlockToRequestor(start_block)
                print(f"Start Block is {start_block} \n End Block is {end_block}")
            
            # self.conn.close()

        except Exception as e:
            #self.conn.close()
            print(f" Error while processing the client request \n {e}")
        
    def startDownload(self,
                  # localport,
                  port,
                  # bindPort
                  ):
        lastBlock = BlockchainDB().lastBlock()

        if not lastBlock:
            GENESISBLOCK = "0000ba684bd73439ce87693ff687c37523c8b6445d9d6266b8a410267ec5ead0"
            #lastBlockHeader = "0000bbe173a3c36eabec25b0574bf7b055db9861b07f9ee10ad796eb06428b9b"
        else:
            lastBlockHeader = lastBlock['BlockHeader']['blockHash']
        
        startBlock = bytes.fromhex(lastBlockHeader)
        
        getHeaders = requestBlock(startBlock=startBlock)
        self.connect = Node(self.host, port)
        self.socket = self.connect.connect(port)

        """
        self.connectToHost(localport, port, bindPort)

        """
        self.connect.send(getHeaders)
        """

        while True:    
            envelope = NetworkEnvelope.parse(self.stream)
            if envelope.command == b"Finished":
                blockObj = FinishedSending.parse(envelope.stream())
                print(f"All Blocks Received")
                self.socket.close()
                break

            if envelope.command == b'portlist':
                ports = portlist.parse(envelope.stream())
                nodeDb = NodeDB()
                portlists = nodeDb.read()

                for port in ports:
                    if port not in portlists:
                        nodeDb.write([port])

            if envelope.command == b'block':
                blockObj = Block.parse(envelope.stream())
                BlockHeaderObj = BlockHeader(blockObj.BlockHeader.version,
                            blockObj.BlockHeader.prevBlockHash, 
                            blockObj.BlockHeader.merkleRoot, 
                            blockObj.BlockHeader.timestamp,
                            blockObj.BlockHeader.bits,
                            blockObj.BlockHeader.nonce)
                
                if BlockHeaderObj.validateBlock():
                    for idx, tx in enumerate(blockObj.Txs):
                        tx.TxId = tx.id()
                        blockObj.Txs[idx] = tx.to_dict()
                
                    BlockHeaderObj.blockHash = BlockHeaderObj.generateBlockHash()
                    BlockHeaderObj.prevBlockHash = BlockHeaderObj.prevBlockHash.hex()
                    BlockHeaderObj.merkleRoot = BlockHeaderObj.merkleRoot.hex()
                    BlockHeaderObj.nonce =  little_endian_to_int(BlockHeaderObj.nonce)
                    BlockHeaderObj.bits = BlockHeaderObj.bits.hex()
                    blockObj.BlockHeader = BlockHeaderObj
                    BlockchainDB().write([blockObj.to_dict()])
                    print(f"Block Received - {blockObj.Height}")
                else:
                    self.secondryChain[BlockHeaderObj.generateBlockHash()] = blockObj
        """