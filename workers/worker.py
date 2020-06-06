import datetime
import hashlib
import paho.mqtt.client as mqtt
import pickle
import socket
from threading import Thread
# from users import Data
# import config
import os
import time
import platform

# mosquitto_pub -h localhost -t test -u admin -P password -n -r -d

# blockchain/worker/chain, blockchain/worker/mine, blockchain/worker/add, blockchain/worker/times,
# blockchain/worker/worker_id/read, blockchain/worker/config

# blockchain/api/block_winner, blockchain/api/notification,
if platform.system() == 'Windows':
    os.system('cls')
else:
    os.system('clear')

print('-----------------------------------')
print('           MINER / WORKER          ')
print('-----------------------------------')

username = 'admin'
password = 'password'
broker_ip = input("Broker's IP: ").strip()
broker_port_no = 1883
topic = 'blockchain/worker/#'
print('-----------------------------------')
chain = []
add_chain = {}   # {tran_id: [{(worker_id, work_time):{data, time, user, nonce, hash}}, ], }
mine_data = {}  # {tran_id: {data, time, user}...}
times = {}   # {tran_id: {w1: time, w2: time}, ...}
vote_poll = {}   # {tran_id: {votes:{worker_id: vote_amt..}, voters:set()}}
read_request = {}   # {req_id: {'user': user, 'type': {all:all}/{'nonce': nonce}/{hash: hash}}}
block_winners = []
client = mqtt.Client()


def ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

worker_id = ip_address()

def on_connect(connect_client, userdata, flags, rc):
    print("Connected with Code :" +str(rc))
    # Subscribe Topic from here
    connect_client.subscribe(topic)


# Callback Function on Receiving the Subscribed Topic/Message
def on_message(message_client, userdata, msg):
    global chain
    # print the message received from the subscribed topic
    print(f'Topic received: {msg.topic}')
    topic_recv = msg.topic
    if (len(chain)==0) and (topic_recv == 'blockchain/worker/chain'):
        chain = pickle.loads(msg.payload)
        print(f'chain received: {chain}')
    elif topic_recv == 'blockchain/worker/mine':       # mine request is sent by web api
        data = pickle.loads(msg.payload)
        # trans_id = block_chain.get_transaction_id(**data)
        # d = {trans_id: data}
        mine_data.update(data)
    elif topic_recv == 'blockchain/worker/add':        # this is sent by workers
        add_data = pickle.loads(msg.payload)    # [worker_id, {data}, trans_id]
        if add_data[0] != worker_id and (add_data[2] in add_chain):
            add_chain[add_data[2]].append({(add_data[0], datetime.datetime.now()): add_data[1]})
        elif add_data[0] != worker_id and (add_data[2] not in add_chain):
            add_chain[add_data[2]] = [{(add_data[0], datetime.datetime.now()): add_data[1]}]
    elif topic_recv == 'blockchain/worker/vote':    # [tran_id, worker_id, who_vote_is_for]
        recv = pickle.loads(msg.payload)
        if recv[0] in vote_poll:
            vote_dict = vote_poll[recv[0]]
            if recv[1] not in vote_dict['voters']:
                vote_dict['voters'].add(recv[1])
                if recv[2] not in vote_dict['votes']:
                    vote_dict['votes'][recv[2]] = 1
                else:
                    vote_dict['votes'][recv[2]] += 1
        else:
            vote_poll[recv[0]] = {'votes': {recv[2]: 1}, 'voters': {recv[1]}}
    elif msg.topic == f'blockchain/worker/{worker_id}/read':
        read_request.update(pickle.loads(msg.payload))


def broker_loop():
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set(username, password)
    client.connect(broker_ip, broker_port_no, 60)
    client.loop_forever()


class Block:

    def __init__(self, data, nonce, user, previous_hash, timestamp):
        self.__data = data
        self.__timestamp = timestamp
        self.__previous_hash = previous_hash
        self.__nonce = nonce
        self.__user = user
        self.__hash = self.get_hash()

    def get_hash(self):
        h = hashlib.sha256()
        h.update(
            str(self.__nonce).encode('utf-8') +
            str(self.__data).encode('utf-8') +
            str(self.__previous_hash).encode('utf-8') +
            str(self.__user).encode('utf-8') +
            str(self.__timestamp).encode('utf-8')
        )

        return h.hexdigest()

    def block_info(self):
        return {'nonce': self.__nonce, 'data': self.__data, 'date': self.__timestamp, 'hash': self.__hash}

    def __str__(self):
        block_dict = self.block_info()
        block = ''
        for i in block_dict:
            block += f'{i} : {block_dict[i]}\n'
        return block


def cleanup(trans_id):
    to_clean = [add_chain, mine_data, times, vote_poll]
    for point in to_clean:
        del point[trans_id]


class BlockChain:
    def __init__(self, admin):
        self.diff = 4  # diff is set to 4, diff controls how easy it is to mine a block
        self.max_nonce = 2 ** 32  # the max nonce that a block can have
        self.chain = chain
        self.admin = admin
        self.con_id = 1    # contract id
        self.verified_claims = {}  # id : {}
        self.add_genesis(admin)

    def add_genesis(self, admin):
        data = {'data':'Genesis', 'nonce':1, 'previous_hash':'0x0', 'timestamp':str(datetime.datetime.now())}
        if len(self.chain) == 0:
            for i in range(self.max_nonce):
                if self.get_hash(user=admin, **data)[:self.diff] == self.diff_string:
                    self.chain.append(Block(user=admin, **data))
                    print('chain: ', self.chain)
                    client.publish('blockchain/worker/chain', pickle.dumps(self.chain), retain=True)
                    block_winners.append(worker_id)
                    client.publish('blockchain/api/block_winner', pickle.dumps(block_winners))
                    break
                else:
                    data['nonce'] += 1
            print(f'Genesis added: {self.chain}')

    @property
    def diff_string(self):
        return ''.join(['0' for _ in range(self.diff)])

    def get_last_block(self):
        return self.chain[-1]

    @staticmethod
    def get_hash(data, nonce, user, previous_hash, timestamp):
        h = hashlib.sha256()
        h.update(
            str(nonce).encode('utf-8') +
            str(data).encode('utf-8') +
            str(previous_hash).encode('utf-8') +
            str(user).encode('utf-8') +
            str(timestamp).encode('utf-8')
        )

        return h.hexdigest()

    def add_block(self, data, user, timestamp):
        previous_hash = self.get_last_block().block_info()['hash']
        print('mining block: ', (data, user, previous_hash, timestamp))
        mined_block = self.mine_block(data, user, previous_hash, timestamp)
        print('checking duration..')
        while True:
            if (datetime.datetime.now() - timestamp) > datetime.timedelta(minutes=2):
                print('duration complete!')
                trans_id = self.get_transaction_id(data, user, timestamp)
                try:
                    votes = vote_poll[trans_id]['votes']
                    winner = max(votes, key=votes.get)  # vote_poll = {tran_id: {votes:{worker_id: vote_amt..}, voters:set()}}
                    print('winner: ', winner)
                except KeyError:
                    print('no votes Received')
                    winner = worker_id
                block_winners.append(winner)
                self.chain.append(mined_block)
                print('block added')
                if winner == worker_id:
                    print(' I am the winner! \nPublishing info ...')
                    client.publish('blockchain/api/block_winner', pickle.dumps(block_winners), retain=True)
                    client.publish('blockchain/worker/chain', pickle.dumps(self.chain), retain=True)
                    new = self.get_last_block().block_info()
                    notify = {'info': 'block added successfully', 'nonce': new['nonce'], 'hash': new['hash']}
                    client.publish('notification', pickle.dumps(notify))
                print('cleaning...')
                cleanup(trans_id)
                print('done!')
                break

    def check_pow(self, data, user, nonce, previous_hash, timestamp, hash_id):
        new_hash = self.get_hash(data, nonce, user, previous_hash, timestamp)
        if (new_hash == hash_id) and (new_hash[:self.diff] == self.diff_string):
            return True
        else:
            return False

    @staticmethod
    def get_transaction_id(data, user, timestamp):
        h = hashlib.sha256()
        h.update(
            str(data).encode('utf-8') +
            str(user).encode('utf-8') +
            str(timestamp).encode('utf-8')
        )

        return h.hexdigest()

    def check_claim(self, trans_id):
        print('mining claim submitted.. \nverifying..')
        previous_hash = self.get_last_block().block_info()['hash']
        for info in add_chain[trans_id]:
            key = list(info.keys())[0]
            print(f'checking pow: {info[key]}')
            if self.check_pow(previous_hash=previous_hash, **info[key]):
                # times = {}   # {tran_id: {w1: time, w2: time}, ...}
                print(f'claim verified | author: {key}')
                if trans_id in times:
                    times[trans_id].update({key[0]: key[1]})
                else:
                    times[trans_id] = {key[0]: key[1]}
            else:
                print(f'False claim | author: {key}')
        # vote = [tran_id, worker_id, who_vote_is_for]
        if trans_id in times:  # if a proof of work has been verified find min time and vote
            candidate = min(times[trans_id], key=times[trans_id].get)
            vote = [trans_id, worker_id, candidate]
            print('casting vote : ', vote)
            # add chain format => {tran_id: [{(worker_id, work_time):{data, time, user, nonce, hash}}, ], }
            for claim_dict in add_chain[trans_id]:
                if (candidate, times[trans_id][candidate]) in claim_dict:
                    data = claim_dict[(candidate, times[trans_id][candidate])]
                    self.verified_claims[trans_id] = data.update({'previous_hash': previous_hash})
            client.publish('blockchain/worker/vote', pickle.dumps(vote))

        #data, add_chain[trans_id]['nonce'], user, previous_hash, timestamp

    def mine_block(self, data, user, previous_hash, timestamp):
        """this function does the block mining, the job of the block mining is to make sure the hash of a block
         matches the given pattern set by the diff_string. """
        trans_id = self.get_transaction_id(data, user, timestamp)
        for nonce in range(self.max_nonce):
            new_hash = self.get_hash(data, nonce, user, previous_hash, timestamp)
            if new_hash[:self.diff] == self.diff_string:
                work = {trans_id: {'data': data, 'user': user, 'timestamp': timestamp,
                                   'nonce': nonce, 'hash_id': hash}}
                print('mining completed: ', work)
                # add_chain -> [worker_id, {data}, trans_id]
                client.publish('blockchain/worker/add', pickle.dumps([worker_id, work, trans_id]))
                vote = [trans_id, worker_id, worker_id]
                client.publish('blockchain/worker/vote', pickle.dumps(vote))

                return Block(data, nonce, user, previous_hash, timestamp)
            elif trans_id in self.verified_claims:     # add chain format => {tran_id: [{(worker_id, work_time):{data, time, user, nonce, hash}}, ], }
                    block = Block(**self.verified_claims[trans_id])
                    del self.verified_claims[trans_id]
                    return block

    def read_block(self, user, nonce=None, hash_=None):  # reading data stored in the block
        if not nonce and not hash_:
            return {'error': 'please specify hash or nonce'}
        elif nonce:
            nones = []
            for block in self.chain:  # checks if nonce in chain
                info = block.block_info()
                if (info['nonce'] == nonce) and (info['user'] == user):
                    nones.append(block.block_info())
            return nones
        elif hash_:
            nones = []
            for block in self.chain:  # checks if hash in chain
                info = block.block_info()
                if (info['hash'] == hash_) and (info['user'] == user):
                    nones.append(block.block_info())
                    return nones
            return [{'error': 'invalid block'}]

    def read_all(self, user):
        if user == self.admin:
            return [block.block_info() for block in self.chain]  # reads all data in chain
        else:
            return [block.block_info() for block in self.chain if block.block_info()['user'] == user]


class BrokerRequest:
    def __init__(self, user, pw, ip, sub_topic):
        self.user = user
        self.pw = pw
        self.ip = ip
        self.port = 1883
        self.topic = sub_topic
        self.response = None
        self.client = mqtt.Client()

    def on_connect(self, connect_client, userdata, flags, rc):
        print("Connected with Code :" + str(rc))
        # Subscribe Topic from here
        connect_client.subscribe(self.topic)

    def on_message(self, message_client, userdata, msg):
        if pickle.loads(msg.payload):
            self.response = pickle.loads(msg.payload)

    def broker_loop(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.username_pw_set(self.user, self.pw)
        self.client.connect(self.ip, self.port, 60)
        self.client.loop_start()
        while True:
            if self.response:
                self.client.loop_stop()
                self.client.disconnect()
                return self.response


def initialization():
    global block_chain
    # store = Data()  # initializing user data
    # super_user = store.get_key(**config.test)  # creating super user
    super_user = BrokerRequest(user=username, pw=password, ip=broker_ip, sub_topic='blockchain/config').broker_loop()
    print('admin: ', super_user)
    block_chain = BlockChain(super_user)  # initializing block chain


def check_mine_request():
    while True:
        if len(mine_data) > 0:
            for trans in mine_data:
                block_chain.add_block(**mine_data[trans])


def check_read_request():
    while True:
        if len(read_request) > 0:
            remove = []
            for req_id in read_request:   # {req_id: {'user': user, 'type': all/{'nonce': nonce}/{hash: hash}}}
                data = read_request[req_id]
                if data['type'] == 'all':
                    notify = {req_id: block_chain.read_all(data['user'])}
                    client.publish('blockchain/api/notification', pickle.dumps(notify))
                    remove.append(req_id)
                elif list(data['type'].keys())[0] in ['nonce', 'hash']:
                    notify = {req_id: block_chain.read_block(data['user'], **data['type'])}
                    client.publish('blockchain/api/notification', pickle.dumps(notify))
                    remove.append(req_id)
                else:
                    notify = {req_id: {'error': 'an error occurred in read_request'}}
                    client.publish('blockchain/api/notification', pickle.dumps(notify))
                    #del read_request[req_id]
                    remove.append(req_id)
            for req_id in remove:
                del read_request[req_id]


def main():
    try:
        h1 = Thread(target=broker_loop)
        h1.start()
        time.sleep(3)
        initialization()
        h2 = Thread(target=check_mine_request)
        h3 = Thread(target=check_read_request)
        h2.start()
        h3.start()

    except KeyboardInterrupt:
        os.system('kill -9 {}'.format(os.getpid()))
        print('Programme Terminated')


if __name__ == '__main__':
    main()

# b = BlockChain()
# b.add_block('emeka')
# b.add_block('james')
# print(b.read_block(nonce=1))
# print(b.read_all())
