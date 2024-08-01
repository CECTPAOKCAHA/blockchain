import sys
sys.path.append('/home/oxana/Desktop/AU/COMP498/blockchain-udemy-adv')

from Blockchain.Backend.core.block import Block
from Blockchain.Backend.core.blockheader import BlockHeader
from Blockchain.Backend.util.util import hash256
from Blockchain.Backend.core.database.database import BlockchainDB
from Blockchain.Backend.core.Tx import CoinbaseTx
from multiprocessing import Process, Manager
from Blockchain.Frontend.run import main
import time

ZERO_HASH = '0' * 64
VERSION = 1

class Blockchain:
    def __init__(self, utxos, MemPool):
        self.utxos = utxos
        self.MemPool = MemPool

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

    """Keep track of all the unspent transactions in cache memory for fast retrieval"""

    def store_utxos_in_cache(self, Transaction):
        self.utxos[Transaction.TxId] = Transaction

    """Read Transactions from Memory Pool"""
    def read_transaction_from_memorypool(self):
        self.TxIds = []
        self.addTransactionsInBlock = []

        for tx in self.MemPool:
            self.TxIds.append(tx)
            self.addTransactionsInBlock.append(self.MemPool[tx])

    def convert_to_json(self):
        self.TxJson = []

        for tx in self.addTransactionsInBlock:
            self.TxJson.append(tx.to_dict())

    def addBlock(self, BlockHeight, prevBlockHash):
        self.read_transaction_from_memorypool()
        timestamp = int(time.time())
        coinbaseInstance = CoinbaseTx(BlockHeight)
        coinbaseTx = coinbaseInstance.CoinbaseTransaction()

        self.TxIds.insert(0, coinbaseTx.TxId)
        self.addTransactionsInBlock.insert(0, coinbaseTx)
        
        merkleRoot = coinbaseTx.TxId
        bits = 'ffff001f'
        blockheader = BlockHeader(VERSION, prevBlockHash, merkleRoot, timestamp, bits)
        blockheader.mine()
        self.store_utxos_in_cache(coinbaseTx)
        self.convert_to_json()
        print(f"Block {BlockHeight} mined successfully with Nonce value of {blockheader.nonce}")
        self.write_on_disk([Block(BlockHeight, 1, blockheader.__dict__, 1, self.TxJson).__dict__])
        

    def main(self):
        lastBlock = self.fetch_last_block()
        if lastBlock is None:
            self.GenesisBlock()
        while True:
            lastBlock = self.fetch_last_block()
            """print(json.dumps(lastBlock, indent=4))"""
            BlockHeight = lastBlock["Height"] + 1
            prevBlockHash = lastBlock['BlockHeader']['BlockHash']
            self.addBlock(BlockHeight, prevBlockHash)

if __name__ == "__main__":
    with Manager() as manager:
        utxos = manager.dict()
        MemPool = manager.dict()

        webapp = Process(target= main, args= (utxos, MemPool))
        webapp.start()

        blockchain = Blockchain(utxos, MemPool)
        blockchain.main()