import datetime
import hashlib


class Block:

    def __init__(self, data, nonce, user, previous_hash=''):
        self.data = data
        self.timestamp = str(datetime.datetime.now())
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.user = user
        self.hash = self.get_hash()

    def get_hash(self):
        h = hashlib.sha256()
        h.update(
            str(self.nonce).encode('utf-8') +
            str(self.data).encode('utf-8') +
            str(self.previous_hash).encode('utf-8') +
            str(self.user).encode('utf-8') +
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
    def __init__(self, admin):
        self.diff = 2                      # diff is set to 2, diff controls how easy it is to mine a block
        self.max_nonce = 2**32             # the max nonce that a block can have
        self.chain = []   # initializing chain with a genesis block
        self.admin = admin
        self.add_genesis(admin)

    def add_genesis(self, admin):
        if len(self.chain) == 0:
            self.chain.append(self.mine_block(Block('Genesis', nonce=1, user=admin)),)

    @property
    def diff_string(self):
        return ''.join(['0' for _ in range(self.diff)])

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, data, user):
        chain_copy = self.chain[:]
        new_block = Block(data, previous_hash=self.get_last_block().hash, nonce=1, user=user)   # to add a block, first the block is initialised with nonce 1
        mined_block = self.mine_block(new_block)  # here block is mined, mining is explained in the mine function
        self.chain.append(mined_block)
        if self.is_chain_valid():
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

    def mine_block(self, block):
        """this function does the block mining, the job of the block mining is to make sure the hash of a block
         matches the given pattern set by the diff_string. """
        for _ in range(self.max_nonce):
            if block.get_hash()[:self.diff] == self.diff_string:
                block.hash = block.get_hash()
                return block
            else:
                block.nonce += 1

    def read_block(self, user, nonce=None, hash_=None):   # reading data stored in the block
        if not nonce and not hash_:
            return {'error': 'please specify hash or nonce'}
        elif nonce:
            nones = []
            for block in self.chain:          # checks if nonce in chain
                if (block.nonce == nonce) and (block.user == user):
                    nones.append(block.block_info())
            return nones
        elif hash_:
            nones = []
            for block in self.chain:          # checks if hash in chain
                if (block.hash == hash_) and (block.user == user):
                    nones.append(block.block_info())
                    return nones
            return [{'error': 'invalid block'}]

    def read_all(self, user):
        if user == self.admin:
            return [block.block_info() for block in self.chain]   # reads all data in chain
        else:
            return [block.block_info() for block in self.chain if block.user == user]

# b = BlockChain()
# b.add_block('emeka')
# b.add_block('james')
# print(b.read_block(nonce=1))
# print(b.read_all())
