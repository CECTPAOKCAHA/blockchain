from Backend.core.block import Block
from Blockchain.Backend.core.network.connection import Node
from Blockchain.Backend.core.database.database import BlockchainDB
from Blockchain.Backend.core.network.network import requestBlock, NetworkEnvelope, FinishedSending
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

            if envelope.command == requestBlock.command:
                start_block, end_block = requestBlock.parse(envelope.stream())
                self.sendBlockToRequestor(start_block)
                logger.info(f"Start Block is {start_block} \n End Block is {end_block}")

        except Exception as e:            
            logger.error(f" Error while processing the client request \n {e}")

    def sendBlockToRequestor(self, start_block):
        logger.debug(f'Trying to sendBlockToRequestor')
        blocksToSend = self.fetchBlocksFromBlockchain(start_block)

        try:
            self.sendBlock(blocksToSend)
            self.sendFinishedMessage()
        except Exception as e:
            logger.error(f"Unable to send the blocks \n {e}")

    def sendFinishedMessage(self):
        logger.debug(f'trying to sendFinishedMessage()')
        try:
            MessageFinish = FinishedSending()
            envelope = NetworkEnvelope(MessageFinish.command, MessageFinish.serialize())
            self.conn.sendall(envelope.serialize())
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
        
    def startDownload(self, port):
        try:
            logger.info(f"Starting download from node at port {port}...")

            # Retrieve the last block from the database
            lastBlock = BlockchainDB().lastBlock()
            if not lastBlock:
                lastBlockHeader = "0000770e3c06bd4f977837b97a430255df8e8202fe816fa1df4e57ea0e3105d9"
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
            self.socket = self.connect.connect(port)
            self.connect.send(getHeaders)
            logger.info(f"Connected to node at port {port} and sent header request.")

            # Continuously read and process the network envelope
            while True:
                logger.debug("Waiting to receive data from the node...")
                self.stream = self.socket.makefile('rb', None)
                envelope = NetworkEnvelope.parse(self.stream)

                # Check if all blocks have been received
                if envelope.command == b"Finished":
                    logger.info("All blocks received.")
                    self.socket.close()
                    break

                # Process the received block
                if envelope.command == b'block':
                    blockObj = Block.parse(envelope.stream())
                    logger.info(f"Block received - Height: {blockObj.Height}")

        except Exception as e:
            logger.error(f"Exception occurred in startDownload: {e}", exc_info=True)
            if hasattr(self, 'socket'):
                self.socket.close()