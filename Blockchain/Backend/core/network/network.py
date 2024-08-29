"""
from base64 import encode
"""
from io import BytesIO
from Blockchain.Backend.util.util import (encode_varint, int_to_little_endian, little_endian_to_int, hash256, read_varint)
import logging

# Assuming the necessary imports are already in place
logger = logging.getLogger(__name__)

NETWORK_MAGIC = b'\xf9\xbe\xb4\xd9'
FINISHED_SENDING =b'\x0a\x11\x09\x07'

class NetworkEnvelope:
    def __init__(self, command, payload):
        self.command = command
        self.payload = payload
        self.magic = NETWORK_MAGIC
        logger.info(f'NetworkEnvelope constructor: Command is {command}')

    

    @classmethod
    def parse(cls, s):
        logger.info("Starting to parse the network envelope...")
        try:
            # Read and verify the magic number
            magic = s.read(4)
            logger.debug(f"Magic number read: {magic.hex()}")

            if magic != NETWORK_MAGIC:
                error_message = f"Magic is not right {magic.hex()} vs {NETWORK_MAGIC.hex()}"
                logger.error(error_message)
                raise RuntimeError(error_message)

            # Read the command
            command = s.read(12)
            command = command.strip(b'\x00')
            logger.debug(f"Command read: {command}")

            # Read and log the payload length
            payloadLen = little_endian_to_int(s.read(4))
            logger.debug(f"Payload length: {payloadLen}")

            # Read the checksum
            checksum = s.read(4)
            logger.debug(f"Checksum read: {checksum.hex()}")

            # Read and log the payload
            payload = s.read(payloadLen)
            logger.debug(f"Payload read: {payload.hex()}")

            # Calculate and verify the checksum
            calculatedChecksum = hash256(payload)[:4]
            logger.debug(f"Calculated checksum: {calculatedChecksum.hex()}")

            if calculatedChecksum != checksum:
                error_message = "Checksum does not match"
                logger.error(error_message)
                raise IOError(error_message)

            logger.info("Parsing completed successfully.")
            return cls(command, payload)

        except Exception as e:
            logger.error(f"Exception occurred in parse: {e}", exc_info=True)
            raise

    
    def serialize(self):
        result = self.magic
        result += self.command + b'\x00' * (12 - len(self.command))
        result += int_to_little_endian(len(self.payload), 4)
        result += hash256(self.payload)[:4]
        result += self.payload
        return result 
    
    def stream(self):
        return BytesIO(self.payload)
    

class requestBlock:
    command = b'requestBlock'

    def __init__(self, startBlock = None, endBlock = None) -> None:
        if startBlock is None:
            raise RuntimeError("Starting Block cannot be None")
        else:
            self.startBlock = startBlock
        
        if endBlock is None:
            self.endBlock = b'\x00' * 32
        else: 
            self.endBlock = endBlock
    
    @classmethod
    def parse(cls, stream):
        startBlock = stream.read(32)
        endBlock = stream.read(32)
        return startBlock, endBlock
    
        
    def serialize(self):
        result = self.startBlock
        result += self.endBlock
        return result 

class portlist:
    command = b'portlist'
    def __init__(self, ports = None):
        self.ports = ports
    
    @classmethod
    def parse(cls, s):
        ports = []
        length = read_varint(s)

        for _ in range(length):
            port = little_endian_to_int(s.read(4))
            ports.append(port)
        
        return ports
        

    def serialize(self):
        result = encode_varint(len(self.ports))

        for port in self.ports:
            result += int_to_little_endian(port, 4)
        
        return result

class FinishedSending:
    command = b'Finished'

    @classmethod
    def parse(cls, s):
        magic = s.read(4)

        if magic == FINISHED_SENDING:
            return "Finished"

    def serialize(self):
        result = FINISHED_SENDING 
        return result 
    