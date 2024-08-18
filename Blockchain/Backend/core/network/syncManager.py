from Blockchain.Backend.core.network.connection import Node
from Blockchain.Backend.core.database.database import BlockchainDB

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



        """
        getHeaders = requestBlock(startBlock=startBlock)
        self.connectToHost(localport, port, bindPort)
        self.connect.send(getHeaders)

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