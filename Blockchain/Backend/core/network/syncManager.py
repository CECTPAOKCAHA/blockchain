from Blockchain.Backend.util.util import little_endian_to_int
from Blockchain.Backend.core.block import Block
from Blockchain.Backend.core.blockheader import BlockHeader
from Blockchain.Backend.core.network.connection import Node
from Blockchain.Backend.core.database.database import BlockchainDB, NodeDB
from Blockchain.Backend.core.network.network import portlist, requestBlock, NetworkEnvelope, FinishedSending
from threading import Thread
import logging

# Create a logger instance for this module
logger = logging.getLogger(__name__)

class syncManager:
    # def __init__(self, host, port, newBlockAvailable = None, secondryChain = None, Mempool = None):
    def __init__(self, host, port):
        self.host = host
        self.port = port 
        logger.debug(f"Constructor: syncManager initialized with host: {self.host}, port: {self.port}")

    def spinUpTheServer(self):
        try:
            self.server = Node(self.host, self.port)
            self.server.startServer()
            logger.info("SERVER STARTED")
            logger.info(f"[LISTENING] at {self.host}:{self.port}")
            
            while True:
                logger.debug("Waiting to accept a connection...")
                self.conn, self.addr = self.server.acceptConnection()
                logger.info(f"Connection accepted from {self.addr}")
                handleConn = Thread(target = self.handleConnection)
                handleConn.start()
        except Exception as e:
            logger.error(f"Exception in spinUpTheServer: {e}", exc_info=True)

    def handleConnection(self):
        envelope = self.server.read()
        try:          
            if len(str(self.addr[1])) == 4:
                self.addNode()
            if envelope.command == requestBlock.command:
                start_block, end_block = requestBlock.parse(envelope.stream())
                self.sendBlockToRequestor(start_block)
                logger.info(f"Start Block is {start_block} \n End Block is {end_block}")

        except Exception as e:            
            logger.error(f" Error while processing the client request \n {e}")

    def addNode(self):
        nodeDb = NodeDB()
        portList = nodeDb.read()

        if self.addr[1] and (self.addr[1] +1) not in portList:
            nodeDb.write([self.addr[1] + 1])    

    def sendBlockToRequestor(self, start_block):
        logger.debug(f'Trying to sendBlockToRequestor')
        blocksToSend = self.fetchBlocksFromBlockchain(start_block)

        try:
            self.sendBlock(blocksToSend)
            self.sendPortlist()
            self.sendFinishedMessage()
        except Exception as e:
            logger.error(f"Unable to send the blocks \n {e}")

    def sendPortlist(self):
        nodeDB = NodeDB()
        portLists = nodeDB.read()

        portLst = portlist(portLists)
        envelope = NetworkEnvelope(portLst.command, portLst.serialize())
        self.conn.sendall(envelope.serialize())

    def sendFinishedMessage(self):
        logger.debug(f'trying to sendFinishedMessage()')
        try:
            MessageFinish = FinishedSending()
            envelope = NetworkEnvelope(MessageFinish.command, MessageFinish.serialize())
            self.conn.sendall(envelope.serialize())
            logger.info(f'All blocks sent.')
        except Exception as e:
            logger.error(f"Unable to sendFinishedMessage()")        

    def sendBlock(self, blockstoSend):
        logger.debug(f'trying to send sendBlock()')
        try:
            for block in blockstoSend:
                cblock = Block.to_obj(block)
                envelope = NetworkEnvelope(cblock.command, cblock.serialize())
                self.conn.sendall(envelope.serialize())
                logger.info(f"Block Sent {cblock.Height}")
        except Exception as e:
            logger.error(f"Unable to sendBlock()")

    def fetchBlocksFromBlockchain(self, start_Block):
        logger.debug(f"Trying to fetchBlocksFromBlockchain()")
        try:
            fromBlocksOnwards = start_Block.hex()

            blocksToSend = []
            blockchain = BlockchainDB()
            blocks = blockchain.read()

            foundBlock = False 
            for block in blocks:
                if block['BlockHeader']['blockHash'] == fromBlocksOnwards:
                    foundBlock = True
                    continue
            
                if foundBlock:
                    blocksToSend.append(block)
            logger.info(f'fetched {len(blocksToSend)} blocks')

            return blocksToSend
        
        except Exception as e:
            logger.error(f"Unable to fetchBlocksFromBlockchain()")
        
    def startDownload(self, localport, port):
        try:
            logger.info(f"Starting download from node at port {port}...")

            # Retrieve the last block from the database
            lastBlock = BlockchainDB().lastBlock()
            if not lastBlock:
                lastBlockHeader = "000037278fb82dd560695c7cd029760bae25f082126573dbebf7bb5ef4509322"
                logger.info(f"No last block found. Using default block header: {lastBlockHeader}")
            else:
                lastBlockHeader = lastBlock['BlockHeader']['blockHash']
                logger.info(f"Last block found with header: {lastBlockHeader}")

            startBlock = bytes.fromhex(lastBlockHeader)

            # Create a request to get headers starting from the last block
            getHeaders = requestBlock(startBlock=startBlock)
            logger.debug(f"Requesting headers starting from block: {startBlock.hex()}")

            # Establish connection to the node
            self.connect = Node(self.host, port)
            self.socket = self.connect.connect(localport)
            self.stream = self.socket.makefile('rb', None)
            self.connect.send(getHeaders)
            logger.info(f"Connected to node at port {port} and sent header request.")

            # Continuously read and process the network envelope
            while True:
                logger.debug("Waiting to receive data from the node...")
                
                envelope = NetworkEnvelope.parse(self.stream)

                # Check if all blocks have been received
                if envelope.command == b"Finished":
                    blockObj = FinishedSending.parse(envelope.stream())
                    logger.info("All blocks received.")
                    self.socket.close()
                    break

                if envelope.command == b'portlist':
                    ports = portlist.parse(envelope.stream())
                    nodeDb = NodeDB()
                    portlists = nodeDb.read()

                    for port in ports:
                        if port not in portlists:
                            nodeDb.write([port])

                # Process the received block
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
                        BlockHeaderObj.nonce = little_endian_to_int(BlockHeaderObj.nonce)
                        BlockHeaderObj.bits = BlockHeaderObj.bits.hex()

                        blockObj.BlockHeader = BlockHeaderObj

                        BlockchainDB().write([blockObj.to_dict()])

                        logger.info(f"Block received - Height: {blockObj.Height}")

                    else:
                        logger.info(f'Chain is broken')
                    
        except Exception as e:
            logger.error(f"Exception occurred in startDownload: {e}", exc_info=True)
            if hasattr(self, 'socket'):
                self.socket.close()