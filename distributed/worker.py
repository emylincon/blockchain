import datetime
import hashlib
import paho.mqtt.client as mqtt
import pickle
import socket
from threading import Thread
import os
import time
import platform
from dotenv import load_dotenv


class BrokerCom:
    @staticmethod
    def on_connect(connect_client, userdata, flags, rc):
        print("Connected with Code :" + str(rc))
        # Subscribe Topic from here
        connect_client.subscribe(topic)

    # Callback Function on Receiving the Subscribed Topic/Message
    @staticmethod
    def on_message(message_client, userdata, msg):
        global chain
        # print the message received from the subscribed topic
        print(f"Topic received: {msg.topic}")
        topic_recv = msg.topic
        if (len(chain) == 0) and (topic_recv == "blockchain/worker/chain"):
            chain = pickle.loads(msg.payload)
            print(f"chain received: {chain}")
        elif topic_recv == "blockchain/worker/mine":  # mine request is sent by web api
            data = pickle.loads(msg.payload)
            mine_data.update(data)
        elif topic_recv == "blockchain/worker/add":  # this is sent by workers
            add_data = pickle.loads(msg.payload)  # [worker_id, {data}, trans_id]
            # print('add recieved:', add_data)
            if add_data[0] != worker_id and (add_data[2] in add_chain):
                time_ = datetime.datetime.now()
                add_chain[add_data[2]].append({(add_data[0], time_): add_data[1]})
                verify = [
                    add_data[0],
                    add_data[1],
                    add_data[2],
                    time_,
                ]  # # [worker_id, {data}, trans_id, time]
                # print('add: ', verify)
                if verify:
                    # print('not none: ', verify)
                    block_chain.check_claim(verify)
            elif add_data[0] != worker_id and (add_data[2] not in add_chain):
                time_ = datetime.datetime.now()
                add_chain[add_data[2]] = [{(add_data[0], time_): add_data[1]}]
                verify = [
                    add_data[0],
                    add_data[1],
                    add_data[2],
                    time_,
                ]  # # [worker_id, {data}, trans_id, time]
                # print('add: ', verify)
                if verify:
                    # print('not none: ', verify)
                    block_chain.check_claim(verify)
        elif (
            topic_recv == "blockchain/worker/vote"
        ):  # [tran_id, worker_id, who_vote_is_for]
            recv = pickle.loads(msg.payload)
            if recv[0] in vote_poll:
                vote_dict = vote_poll[recv[0]]
                if recv[1] not in vote_dict["voters"]:
                    vote_dict["voters"].add(recv[1])
                    if recv[2] not in vote_dict["votes"]:
                        vote_dict["votes"][recv[2]] = 1
                    else:
                        vote_dict["votes"][recv[2]] += 1
            else:
                vote_poll[recv[0]] = {"votes": {recv[2]: 1}, "voters": {recv[1]}}
        elif msg.topic == f"blockchain/worker/{worker_id}/read":
            read_request.update(pickle.loads(msg.payload))

    @staticmethod
    def broker_loop():
        client.on_connect = BrokerCom.on_connect
        client.on_message = BrokerCom.on_message

        # client.username_pw_set(username, password)
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
            str(self.__nonce).encode("utf-8")
            + str(self.__data).encode("utf-8")
            + str(self.__previous_hash).encode("utf-8")
            + str(self.__user).encode("utf-8")
            + str(self.__timestamp).encode("utf-8")
        )

        return h.hexdigest()

    def block_info(self):
        return {
            "nonce": self.__nonce,
            "data": self.__data,
            "date": self.__timestamp,
            "hash": self.__hash,
            "user": self.__user,
        }

    def __str__(self):
        block_dict = self.block_info()
        block = ""
        for i in block_dict:
            block += f"{i} : {block_dict[i]}\n"
        return block


def cleanup(trans_id):
    to_clean = [add_chain, mine_data, times, vote_poll]
    for point in to_clean:
        if trans_id in point:
            del point[trans_id]


class BlockChain:
    def __init__(self, admin):
        self.diff = 4  # diff is set to 4, diff controls how easy it is to mine a block
        self.max_nonce = 2**32  # the max nonce that a block can have
        self.chain = chain
        self.admin = admin
        self.con_id = 1  # contract id
        self.verified_claims = {}  # id : {}
        self.add_genesis(admin)
        self.mining = 0

    def add_genesis(self, admin):
        data = {
            "data": "Genesis",
            "nonce": 1,
            "previous_hash": "0x0",
            "timestamp": str(datetime.datetime.now()),
        }
        if len(self.chain) == 0:
            for i in range(self.max_nonce):
                if self.get_hash(user=admin, **data)[: self.diff] == self.diff_string:
                    self.chain.append(Block(user=admin, **data))
                    print("chain: ", self.chain)
                    client.publish(
                        "blockchain/worker/chain", pickle.dumps(self.chain), retain=True
                    )
                    block_winners.append(worker_id)
                    client.publish(
                        "blockchain/api/block_winner", pickle.dumps(block_winners)
                    )
                    break
                else:
                    data["nonce"] += 1
            print(f"Genesis added: {self.chain}")

    @property
    def diff_string(self):
        return "".join(["0" for _ in range(self.diff)])

    def get_last_block(self):
        return self.chain[-1]

    @staticmethod
    def get_hash(data, nonce, user, previous_hash, timestamp):
        h = hashlib.sha256()
        h.update(
            str(nonce).encode("utf-8")
            + str(data).encode("utf-8")
            + str(previous_hash).encode("utf-8")
            + str(user).encode("utf-8")
            + str(timestamp).encode("utf-8")
        )

        return h.hexdigest()

    def add_block(self, data, user, timestamp):
        previous_hash = self.get_last_block().block_info()["hash"]
        print("mining block: ", (data, user, previous_hash, timestamp))
        mined_block = self.mine_block(data, user, previous_hash, timestamp)
        trans_id = self.get_transaction_id(data, user, timestamp)
        self.election(trans_id)
        print("checking voting Timeout..")
        while True:
            if (datetime.datetime.now() - timestamp) > datetime.timedelta(seconds=5):
                print("duration complete!")
                try:
                    votes = vote_poll[trans_id]["votes"]
                    print("votes: ", votes)
                    winner = max(
                        votes, key=votes.get
                    )  # vote_poll = {tran_id: {votes:{worker_id: vote_amt..}, voters:set()}}
                    print("winner: ", winner)
                except KeyError:
                    print("no votes Received")
                    winner = worker_id
                block_winners.append(winner)
                self.chain.append(mined_block)
                print("block added")
                if winner == worker_id:
                    print(" I am the winner! \nPublishing info ...")
                    client.publish(
                        "blockchain/api/block_winner",
                        pickle.dumps(block_winners),
                        retain=True,
                    )
                    client.publish(
                        "blockchain/worker/chain", pickle.dumps(self.chain), retain=True
                    )
                    new = self.get_last_block().block_info()
                    trans_times = {k: str(v) for k, v in times.get(trans_id).items()}
                    notify = {
                        trans_id: {
                            "info": "block added successfully",
                            "nonce": new["nonce"],
                            "hash": new["hash"],
                            "times": trans_times,
                        }
                    }
                    client.publish("blockchain/api/notification", pickle.dumps(notify))
                    print("\n\nTimes: ", times.get(trans_id), "\n\n")
                clean.append(trans_id)
                break

    def check_pow(self, data, user, nonce, previous_hash, timestamp, hash_id):
        new_hash = self.get_hash(data, nonce, user, previous_hash, timestamp)
        if (new_hash == hash_id) and (new_hash[: self.diff] == self.diff_string):
            return True
        else:
            return False

    @staticmethod
    def get_transaction_id(data, user, timestamp):
        h = hashlib.sha256()
        h.update(
            str(data).encode("utf-8")
            + str(user).encode("utf-8")
            + str(timestamp).encode("utf-8")
        )

        return h.hexdigest()

    @staticmethod
    def election(trans_id):
        # vote = [tran_id, worker_id, who_vote_is_for]
        # if a proof of work has been verified find min time and vote
        if trans_id in times:
            print("times: ", times[trans_id])
            candidate = min(times[trans_id], key=times[trans_id].get)
            vote = [trans_id, worker_id, candidate]
            print("casting vote : ", vote)
            client.publish("blockchain/worker/vote", pickle.dumps(vote))
        else:
            print(f"error trans_id :{trans_id} not in times :{times}")

        # data, add_chain[trans_id]['nonce'], user, previous_hash, timestamp

    def check_claim(self, verify):
        # verify = [worker_id, {data}, trans_id, time]
        print("mining claim submitted.. \nverifying..")
        previous_hash = self.get_last_block().block_info()["hash"]

        print(f"checking pow: {verify}")
        if self.check_pow(previous_hash=previous_hash, **verify[1]):
            # times = {}   # {tran_id: {w1: time, w2: time}, ...}
            if (verify[2] not in self.verified_claims) and (self.mining == 1):
                to_add = {"previous_hash": previous_hash, **verify[1]}
                if (
                    len(to_add) == 5
                ):  # checks if variables are complete,bcos pickle objs are very sensitive to change
                    self.verified_claims[verify[2]] = to_add
            print(f"claim verified | author: {verify[0]}")
            if verify[2] in times:
                times[verify[2]].update({verify[0]: verify[-1]})

            else:
                times[verify[2]] = {verify[0]: verify[-1]}
        else:
            print(f"False claim | author: {verify[0]}")

    def mine_block(self, data, user, previous_hash, timestamp):
        """this function does the block mining, the job of the block mining is to make sure the hash of a block
        matches the given pattern set by the diff_string."""
        self.mining = 1
        trans_id = self.get_transaction_id(data, user, timestamp)
        for nonce in range(self.max_nonce):
            new_hash = self.get_hash(data, nonce, user, previous_hash, timestamp)
            if new_hash[: self.diff] == self.diff_string:
                work = {
                    "data": data,
                    "user": user,
                    "timestamp": timestamp,
                    "nonce": nonce,
                    "hash_id": new_hash,
                }
                print("mining completed: ", work)
                self.mining = 0
                # add_chain -> [worker_id, {data}, trans_id]
                send = pickle.dumps([worker_id, work, trans_id])
                print("sending add:", [worker_id, work, trans_id])
                client.publish("blockchain/worker/add", send)
                # adding worker finishing time
                if trans_id in times:
                    times[trans_id].update({worker_id: datetime.datetime.now()})
                else:
                    times[trans_id] = {worker_id: datetime.datetime.now()}
                # vote = [trans_id, worker_id, worker_id]
                # client.publish('blockchain/worker/vote', pickle.dumps(vote))

                return Block(data, nonce, user, previous_hash, timestamp)
            elif (
                trans_id in self.verified_claims
            ):  # add chain format => {tran_id: [{(worker_id, work_time):{data, time, user, nonce, hash}}, ], }
                block = Block(**self.verified_claims[trans_id])
                self.mining = 0
                del self.verified_claims[trans_id]
                return block

    def read_block(
        self, user, nonce=None, hash_=None
    ):  # reading data stored in the block
        if not nonce and not hash_:
            return {"error": "please specify hash or nonce"}
        elif nonce:
            nones = []
            for block in self.chain:  # checks if nonce in chain
                info = block.block_info()
                if (info["nonce"] == nonce) and (info["user"] == user):
                    nones.append(block.block_info())
            return nones
        elif hash_:
            nones = []
            for block in self.chain:  # checks if hash in chain
                info = block.block_info()
                if (info["hash"] == hash_) and (info["user"] == user):
                    nones.append(block.block_info())
                    return nones
            return [{"error": "invalid block"}]

    def read_all(self, user):
        if user == self.admin:
            return [
                block.block_info() for block in self.chain
            ]  # reads all data in chain
        else:
            return [
                block.block_info()
                for block in self.chain
                if block.block_info()["user"] == user
            ]


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

        # self.client.username_pw_set(self.user, self.pw)
        self.client.connect(self.ip, self.port, 60)
        self.client.loop_start()
        while True:
            if self.response:
                self.client.loop_stop()
                self.client.disconnect()
                return self.response

    def __del__(self):
        print("BrokerRequest Object Deleted!")


class Util:
    @staticmethod
    def initialization():
        br = BrokerRequest(
            user=username, pw=password, ip=broker_ip, sub_topic="blockchain/config"
        )
        super_user = br.broker_loop()
        del br
        print("admin: ", super_user)
        block_chain = BlockChain(super_user)  # initializing block chain
        return block_chain

    @staticmethod
    def check_mine_request():
        while True:
            if len(mine_data) > 0:
                for trans in mine_data:
                    block_chain.add_block(**mine_data[trans])
                print("cleaning...")
                for i in clean:
                    cleanup(i)
                print("done!")

    @staticmethod
    def ip_address() -> str:
        hostname = socket.gethostname()
        ip_addr = socket.gethostbyname(hostname)
        return ip_addr

    @staticmethod
    def check_read_request():
        while True:
            if len(read_request) > 0:
                remove = []
                for (
                    req_id
                ) in (
                    read_request
                ):  # {req_id: {'user': user, 'type': all/{'nonce': nonce}/{hash: hash}}}
                    data = read_request[req_id]
                    if data["type"] == "all":
                        notify = {req_id: block_chain.read_all(data["user"])}
                        client.publish(
                            "blockchain/api/notification", pickle.dumps(notify)
                        )
                        remove.append(req_id)
                    elif list(data["type"].keys())[0] in ["nonce", "hash"]:
                        notify = {
                            req_id: block_chain.read_block(data["user"], **data["type"])
                        }
                        client.publish(
                            "blockchain/api/notification", pickle.dumps(notify)
                        )
                        remove.append(req_id)
                    else:
                        notify = {
                            req_id: {"error": "an error occurred in read_request"}
                        }
                        client.publish(
                            "blockchain/api/notification", pickle.dumps(notify)
                        )
                        remove.append(req_id)
                for req_id in remove:
                    del read_request[req_id]


def main():
    global block_chain
    try:
        h1 = Thread(target=BrokerCom.broker_loop)
        h1.start()
        time.sleep(3)
        block_chain = Util.initialization()
        h2 = Thread(target=Util.check_mine_request)
        h3 = Thread(target=Util.check_read_request)
        h2.start()
        h3.start()

    except KeyboardInterrupt:
        os.system("kill -9 {}".format(os.getpid()))
        print("Programme Terminated")


if __name__ == "__main__":
    load_dotenv()  # take environment variables from .env
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

    print("-----------------------------------")
    print("           MINER / WORKER          ")
    print("-----------------------------------")

    username = os.getenv("BROKER_USERNAME")
    password = os.getenv("BROKER_PASSWORD")
    broker_ip = os.getenv("BROKER_IP")
    broker_port_no = int(os.getenv("BROKER_PORT"))
    topic = "blockchain/worker/#"
    print("-----------------------------------")
    chain = []
    add_chain = (
        {}
    )  # {tran_id: [{(worker_id, work_time):{data, time, user, nonce, hash}}, ], }
    mine_data = {}  # {tran_id: {data, time, user}...}
    times = {}  # {tran_id: {w1: time, w2: time}, ...}
    vote_poll = {}  # {tran_id: {votes:{worker_id: vote_amt..}, voters:set()}}
    read_request = (
        {}
    )  # {req_id: {'user': user, 'type': {all:all}/{'nonce': nonce}/{hash: hash}}}
    block_winners = []
    client = mqtt.Client()
    clean = []
    worker_id = Util.ip_address()
    main()
