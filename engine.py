import datetime
import hashlib


class Block:

    def __init__(self, data, nonce, previous_hash=''):
        self.data = data
        self.timestamp = str(datetime.datetime.now())
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.get_hash()

    def get_hash(self):
        h = hashlib.sha256()
        h.update(
            str(self.nonce).encode('utf-8') +
            str(self.data).encode('utf-8') +
            str(self.previous_hash).encode('utf-8') +
            str(self.timestamp).encode('utf-8')
        )

        return h.hexdigest()

    def block_info(self):
        return {'nonce': self.nonce, 'data': self.data, 'date': self.timestamp, 'hash': self.hash}

    def __str__(self):
        block_dict = self.block_info()
        block = ''
        for i in block_dict:
            block += f'{i} : {block_dict[i]}\n'
        return block


class BlockChain:
    def __init__(self):
        self.nonce = 1      # initialization of the nonce
        self.chain = [Block('Genisis', self.nonce), ]
        self.nonce += 1     # nonce is incremented after each addition to chain

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        chain_copy = self.chain[:]
        self.chain.append(Block(data, previous_hash=self.get_last_block().hash, nonce=self.nonce))
        if self.is_chain_valid():
            self.nonce += 1    # nonce is incremented after each addition to chain
            return {'info': 'block added successfully', 'nonce': self.get_last_block().nonce,
                    'hash': self.get_last_block().hash}
        else:
            self.chain = chain_copy[:]
            return {'info': 'Error detected, block not added'}

    def is_chain_valid(self):        # checks if chain has been compromised, this is called after each addition to chain
        for i in range(1, len(self.chain)):
            prevb = self.chain[i - 1]
            currb = self.chain[i]
            if currb.hash != currb.get_hash():
                print('invalid block')
                return False
            if currb.previous_hash != prevb.hash:
                print('invalid chain')
                return False
        return True

    def read_block(self, nonce=None, hash_=None):   # reading data stored in the block
        if not nonce and not hash_:
            return {'error': 'please specify hash or nonce'}
        elif nonce:
            if (nonce <= len(self.chain)) and (nonce > 0):   # checks if nonce is valid
                return self.chain[nonce - 1].block_info()
            else:
                return {'error': f'invalid nonce. Nonce length is {len(self.chain)}'}
        elif hash:
            for block in self.chain:          # checks if hash in chain
                if block.hash == hash:
                    return block.block_info()
            return {'error': 'invalid block'}

    def read_all(self):
        return [block.block_info() for block in self.chain]   # reads all data in chain

# b = BlockChain()
# b.add_block('emeka')
# b.add_block('james')
# print(b.read_block(nonce=1))
# print(b.read_all())
