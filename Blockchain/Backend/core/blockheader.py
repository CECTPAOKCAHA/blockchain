from Blockchain.Backend.util.util import hash256
class BlockHeader:
    def __init__(self, version, prevBlockHash, merkleRoot, timestamp, bits):
        self.version = version
        self.prevBlockHash = prevBlockHash
        self.merkleRoot = merkleRoot
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = 0
        self.BlockHash = ''

    def mine(self):
        while (self.BlockHash[0:4]) != '0000':
            header_string = (
                str(self.version) + 
                self.prevBlockHash + 
                self.merkleRoot + 
                str(self.timestamp) + 
                self.bits + 
                str(self.nonce)
            )
            header_bytes = header_string.encode('utf-8') # convert the string to bytes
            self.BlockHash = hash256(header_bytes).hex()
            self.nonce += 1
            print(f"Mining started {self.nonce}", end= '\r')


