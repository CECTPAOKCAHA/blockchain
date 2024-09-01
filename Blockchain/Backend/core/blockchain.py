import sys
sys.path.append('/home/oxana/Desktop/AU/COMP498/blockchain-udemy-adv')

import logging
import logging.config
import copy
import configparser
from Blockchain.Backend.core.block import Block
from Blockchain.Backend.core.blockheader import BlockHeader
from Blockchain.Backend.util.util import hash256, target_to_bits, bits_to_target
from Blockchain.Backend.core.database.database import BlockchainDB, NodeDB
from Blockchain.Backend.core.Tx import CoinbaseTx
from Blockchain.Backend.util.util import merkle_root
from multiprocessing import Process, Manager
from Blockchain.Frontend.run import main
from Blockchain.Backend.core.network.syncManager import syncManager
import time

ZERO_HASH = '0' * 64
VERSION = 1
INITIAL_TARGET = 0x0000FFFF00000000000000000000000000000000000000000000000000000000
MAX_TARGET     = 0x0000ffff00000000000000000000000000000000000000000000000000000000
"""
# Calculate new Target to keep our Block mine time under 20 seconds
# Reset Block Difficulty after every 10 Blocks
"""
AVERAGE_BLOCK_MINE_TIME = 20
RESET_DIFFICULTY_AFTER_BLOCKS = 10
AVERAGE_MINE_TIME = AVERAGE_BLOCK_MINE_TIME * RESET_DIFFICULTY_AFTER_BLOCKS

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("blockchain_system.log", mode='w'),  # Log to a file
        logging.StreamHandler()  # Optional: Also log to the console
    ]
)

# Create a logger instance for the main script
logger = logging.getLogger(__name__)

class Blockchain:
    def __init__(self, utxos, MemPool, newBlockAvailable, secondryChain):
        self.utxos = utxos
        self.MemPool = MemPool
        self.newBlockAvailable = newBlockAvailable
        self.secondryChain = secondryChain
        self.current_target = INITIAL_TARGET
        self.bits = target_to_bits(INITIAL_TARGET)

    def write_on_disk(self, block):
        blockchainDB = BlockchainDB()
        blockchainDB.write(block)
        
    def fetch_last_block(self):
        blockchainDB = BlockchainDB()
        return blockchainDB.lastBlock()

    def GenesisBlock(self):
        BlockHeight = 0
        prevBlockHash = ZERO_HASH
        self.addBlock(BlockHeight, prevBlockHash)

  
    """ Start the Sync Node """
    def startSync(self, block = None):
        """ Start the Sync Node """
        logger.info("Starting sync process...")

        try:
        
            node = NodeDB()
            portList = node.read()
            logger.debug(f"Retrieved port list from NodeDB: {portList}")

            for port in portList:
                if localHostPort != port:
                    logger.info(f"Syncing with node at port {port}")
                    sync = syncManager(localHost, port, secondryChain = self.secondryChain)
                    try:
                        if block:
                            sync.publishBlock(localHostPort -1, port, block)
                        else:
                            sync.startDownload(localHostPort -1, port, True)                    
                            logger.info(f"Sync with node at port {port} completed successfully")
                    except Exception as err:
                        logger.error(f'Error while publishing or Downloading a Blockchain\n{err}')

        except Exception as e:
            logger.error(f"Error while downloading the Blockchain (startSync): {e}", exc_info=True)

    """Keep track of all the unspent transactions in cache memory for fast retrieval"""

    def store_utxos_in_cache(self):
        for tx in self.addTransactionsInBlock:
            print(f"Transaction added {tx.TxId}")
            self.utxos[tx.TxId] = tx

    def remove_spent_Transactions(self):
        for txId_index in self.remove_spent_transactions:            
            if txId_index[0].hex() in self.utxos:

                if len(self.utxos[txId_index[0].hex()].tx_outs) < 2:
                    print(f" Spent Transaction removed {txId_index[0].hex()} ")
                    del self.utxos[txId_index[0].hex()]
                else:
                    prev_trans = self.utxos[txId_index[0].hex()]
                    self.utxos[txId_index[0].hex()] = prev_trans.tx_outs.pop(txId_index[1])
                    
    """ Check if it is a double spending Attempt """
    """
    def doubleSpendingAttempt(self, tx):
        for txin in tx.tx_ins:
            if txin.prev_tx not in self.prevTxs and txin.prev_tx.hex() in self.utxos:
                self.prevTxs.append(txin.prev_tx)
            else:
                return True
    """


    """Read Transactions from Memory Pool"""
    def read_transaction_from_memorypool(self):
        self.Blocksize = 80
        self.TxIds = []
        self.addTransactionsInBlock = []
        self.remove_spent_transactions = []

        for tx in self.MemPool:
            self.TxIds.append(bytes.fromhex(tx))
            self.addTransactionsInBlock.append(self.MemPool[tx])
            self.Blocksize += len(self.MemPool[tx].serialize())

            for spent in self.MemPool[tx].tx_ins:
                self.remove_spent_transactions.append([spent.prev_tx, spent.prev_index])


    """ Remove Transactions from Memory pool """
    def remove_transactions_from_memorypool(self):
        for tx in self.TxIds:
            if tx.hex() in self.MemPool:
                del self.MemPool[tx.hex()]


    def convert_to_json(self):
        self.TxJson = []

        for tx in self.addTransactionsInBlock:
            self.TxJson.append(tx.to_dict())
    
    def calculate_fee(self):
        self.input_amount = 0
        self.output_amount = 0
        """ Calculate Input Amount """
        for TxId_index in self.remove_spent_transactions:
            if TxId_index[0].hex() in self.utxos:
                self.input_amount += self.utxos[TxId_index[0].hex()].tx_outs[TxId_index[1]].amount

        """ Calculate Output Amount """
        for tx in self.addTransactionsInBlock:
            for tx_out in tx.tx_outs:
                self.output_amount += tx_out.amount

        self.fee = self.input_amount - self.output_amount

    def settargetWhileBooting(self):
        bits, timestamp = self.getTargetDifficultyAndTimestamp()
        self.bits = bytes.fromhex(bits)
        self.current_target = bits_to_target(self.bits)

    def getTargetDifficultyAndTimestamp(self, BlockHeight = None):
        if BlockHeight:
            blocks = BlockchainDB().read()
            bits = blocks[BlockHeight]['BlockHeader']['bits']
            timestamp = blocks[BlockHeight]['BlockHeader']['timestamp']
        else:
            block = BlockchainDB().lastBlock()
            bits = block['BlockHeader']['bits']
            timestamp = block['BlockHeader']['timestamp']
        return bits, timestamp

    def adjustTargetDifficulty(self, BlockHeight):
        if BlockHeight % 10 == 0:
            bits, timestamp = self.getTargetDifficultyAndTimestamp(BlockHeight - 10)
            Lastbits, lastTimestamp = self.getTargetDifficultyAndTimestamp()

            lastTarget = bits_to_target(bytes.fromhex(bits))
            AverageBlockMineTime = lastTimestamp - timestamp
            timeRatio = AverageBlockMineTime / AVERAGE_MINE_TIME

            NEW_TARGET = int(format(int(lastTarget * timeRatio)))

            if NEW_TARGET > MAX_TARGET:
                NEW_TARGET = MAX_TARGET
            
            self.bits = target_to_bits(NEW_TARGET)
            self.current_target = NEW_TARGET

    def BroadcastBlock(self, block):
        self.startSync(block)       

    def LostCompetition(self):
        deleteBlock = []
        tempBlocks = dict(self.newBlockAvailable)

        for newblock in tempBlocks:
            block = tempBlocks[newblock]
            deleteBlock.append(newblock)

            BlockHeaderObj = BlockHeader(block.BlockHeader.version,
                                    block.BlockHeader.prevBlockHash,
                                    block.BlockHeader.merkleRoot,
                                    block.BlockHeader.timestamp,
                                    block.BlockHeader.bits,
                                    block.BlockHeader.nonce)
            
            if BlockHeaderObj.validateBlock(): 
                for idx, tx in enumerate(block.Txs):
                    self.utxos[tx.id()] = tx.serialize()
                    block.Txs[idx].TxId = tx.id()
                    block.Txs[idx] = tx.to_dict()

                block.BlockHeader.to_hex()
                BlockchainDB().write([block.to_dict()])
            else:
                if self.secondryChain:
                    addBlocks = []
                    addBlocks.append(block) ###
                    prevBlockhash = block.BlockHeader.prevBlockHash.hex()
                    count = 0

                    while count != len(self.secondryChain):
                        if prevBlockhash in self.secondryChain:
                            addBlocks.append(self.secondryChain[prevBlockhash])
                            prevBlockhash = self.secondryChain[prevBlockhash].BlockHeader.prevBlockHash.hex()
                        count += 1

                    blockchain = BlockchainDB().read()
                    lastValidBlock = blockchain[-len(addBlocks)]

                    if lastValidBlock['BlockHeader']['blockHash'] == prevBlockhash:
                        for i in range(len(addBlocks) - 1):
                            orphanBlock = blockchain.pop()

                            for tx in orphanBlock['Txs']:
                                if tx['TxId'] in self.utxos:
                                    del self.utxos[tx['TxId']]


                        BlockchainDB().update(blockchain)

                        for Bobj in addBlocks[::-1]:
                            validBlock = copy.deepcopy(Bobj)
                            validBlock.BlockHeader.to_hex()

                            for index, tx in enumerate(validBlock.Txs):
                                validBlock.Txs[index].TxId = tx.id()
                                validBlock.Txs[index] = tx.to_dict()

                            BlockchainDB().write([validBlock.to_dict()])

                self.secondryChain[newblock] = block

        for blockHash in deleteBlock:
            del self.newBlockAvailable[blockHash]

    def addBlock(self, BlockHeight, prevBlockHash):
        self.read_transaction_from_memorypool()
        self.calculate_fee()
        timestamp = int(time.time())
        coinbaseInstance = CoinbaseTx(BlockHeight)
        coinbaseTx = coinbaseInstance.CoinbaseTransaction()
        self.Blocksize += len(coinbaseTx.serialize())

        coinbaseTx.tx_outs[0].amount = coinbaseTx.tx_outs[0].amount + self.fee    

        self.TxIds.insert(0, bytes.fromhex(coinbaseTx.id()))
        self.addTransactionsInBlock.insert(0, coinbaseTx)
        
        merkleRoot = merkle_root(self.TxIds)[::-1].hex()
        self.adjustTargetDifficulty(BlockHeight)
        blockheader = BlockHeader(VERSION, prevBlockHash, merkleRoot, timestamp, self.bits, nonce=0)
        competitionOver = blockheader.mine(self.current_target, self.newBlockAvailable)

        if competitionOver:
            self.LostCompetition()
        else:            
            newBlock = Block(BlockHeight, 
                            self.Blocksize, 
                            blockheader, 
                            len(self.addTransactionsInBlock),
                            self.addTransactionsInBlock
                            )
            blockheader.to_bytes()
            self.BroadcastBlock(newBlock)
            blockheader.to_hex()
            time.sleep(5) # Add a 5-second delay here
            self.remove_spent_Transactions()
            self.remove_transactions_from_memorypool()
            self.store_utxos_in_cache( )
            self.convert_to_json()
            print(f"Block {BlockHeight} mined successfully with Nonce value of {blockheader.nonce}")
            self.write_on_disk([Block(BlockHeight, 
                                      self.Blocksize, 
                                      blockheader.__dict__, 
                                      len(self.TxJson), 
                                      self.TxJson).__dict__]
                                      )
        

    def main(self):
        lastBlock = self.fetch_last_block()
        if lastBlock is None:
            self.GenesisBlock()
        while True:
            lastBlock = self.fetch_last_block()
            """print(json.dumps(lastBlock, indent=4))"""
            BlockHeight = lastBlock["Height"] + 1
            prevBlockHash = lastBlock['BlockHeader']['blockHash']
            self.addBlock(BlockHeight, prevBlockHash)

if __name__ == "__main__":
    """ read configuration file """
    logger.info("Starting the blockchain system...")
    try: 
        config = configparser.ConfigParser()
        config.read('config.ini')
        localHost = config['DEFAULT']['host']
        localHostPort = int(config['MINER']['port'])
        webport = int(config['Webhost']['port'])

        logger.info(f"Configuration loaded. Local Host: {localHost}, Local Host Port: {localHostPort}, Web Port: {webport}")

        with Manager() as manager:
            utxos = manager.dict()
            MemPool = manager.dict()
            newBlockAvailable = manager.dict()
            secondryChain = manager.dict()

            webapp = Process(target= main, args= (utxos, MemPool, webport))
            webapp.start()
            logger.info("Web app process started.")

            """ Start Server and Listen for miner requests """
            sync = syncManager(localHost, localHostPort, newBlockAvailable, secondryChain)
            startServer = Process(target = sync.spinUpTheServer)
            startServer.start()
            logger.info("Sync server process started.")


            blockchain = Blockchain(utxos, MemPool, newBlockAvailable, secondryChain)
            blockchain.settargetWhileBooting()
            blockchain.startSync()
            blockchain.main()
    except Exception as e:
        logger.error(f"Exception in main execution block: {e}", exc_info=True)