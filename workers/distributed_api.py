from flask import Flask, request, make_response
from flask_restful import Resource, Api
import ast
import json
from users import Data
from functools import wraps
import config
import pickle
import paho.mqtt.client as mqtt
import hashlib
import datetime
from threading import Thread

# cd home/ ; git clone https://github.com/emylincon/blockchain ; cd blockchain/workers

# blockchain/worker/chain, blockchain/worker/mine, blockchain/worker/add, blockchain/worker/times,
# blockchain/worker/worker_id/read

# blockchain/api/block_winner, blockchain/api/notification,


print('-----------------------------------')
print('        BLOCK CHAIN JSON API       ')
print('-----------------------------------')

username = 'admin'
password = 'password'
broker_ip = '192.168.40.180'
broker_port_no = 1883
topic = 'blockchain/api/#'
print('-----------------------------------')

app = Flask(__name__)
api = Api(app)                # initializing app
store = Data()                # initializing user data
admin = store.get_key(**config.test)     # creating super user
winner = ''
notify = {}    # id : data
client = mqtt.Client()


def on_connect(connect_client, userdata, flags, rc):
    print("Connected with Code :" +str(rc))
    # Subscribe Topic from here
    connect_client.subscribe(topic)


# Callback Function on Receiving the Subscribed Topic/Message
def on_message(message_client, userdata, msg):
    global winner

    # print the message received from the subscribed topic
    print('top: ', msg.topic)
    topic_recv = msg.topic.split('/')[-1]
    print('topic received:', topic_recv)
    if topic_recv == 'block_winner':
        winners = pickle.loads(msg.payload)
        print(f'winners: {winners} \nWinner: {winners[-1]}')
        winner = winners[-1]

    elif topic_recv == 'notification':
        notify.update(pickle.loads(msg.payload))
        print(notify)


def broker_loop():
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set(username, password)
    client.connect(broker_ip, broker_port_no, 60)
    client.loop_forever()


def auth_required(f):           # user verification authentication
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        try:
            if auth:
                if store.verify(store.get_key(auth.username, auth.password)):
                    return f(*args, **kwargs)

            return json.dumps({"error": "could not verify login"})
        except Exception:
            return json.dumps({"error": "could not verify login"})

    return decorated


class HomePage(Resource):
    @staticmethod
    def get():
        return {'about': 'Welcome to Emeka\'s implementation of blockchain! To Register use endpoint=> register/'}


class Register(Resource):       # Registration resource
    @staticmethod
    def post():          # user sends a json containing username & password -> {"user": "john", "pw": "pass"}
        try:
            reg_data = request.get_json()
            if set(reg_data.keys()) == {'user', 'pw'}:   # checks if format is followed
                if store.add_item(**reg_data) == 1:
                    return json.dumps({'info': f'registration successful for {reg_data["user"]}'})
                else:
                    return json.dumps({'error': f'Error {reg_data["user"]} already exists'})
            else:
                return json.dumps({'error': 'invalid data sent: format -> {"user": "john", "pw": "pass"}'})
        except AttributeError:
            return json.dumps({'error': 'invalid data sent: format -> {"user": "john", "pw": "pass"}'})


def get_transaction_id(data, user, timestamp):
    h = hashlib.sha256()
    h.update(
        str(data).encode('utf-8') +
        str(user).encode('utf-8') +
        str(timestamp).encode('utf-8')
    )

    return h.hexdigest()


class AddBlock(Resource):
    @staticmethod
    @auth_required
    def post():
        user = store.get_key(request.authorization.username, request.authorization.password)
        sent_data = request.get_json()
        if sent_data != '':
            mine = {'data': sent_data, 'user': user, 'timestamp': datetime.datetime.now()}
            trans_id = get_transaction_id(**mine)
            pub = {trans_id: mine}
            client.publish('blockchain/worker/mine', pickle.dumps(pub))
            print(f'published: {pub}')
            return json.dumps(get_response(trans_id))
        else:
            return {'error': 'no data sent'}


def get_response(trans_id):
    while True:
        if trans_id in notify:
            response = notify[trans_id]
            del notify[trans_id]
            return response


class Read(Resource):
    @staticmethod
    @auth_required
    def get(text):
        user = store.get_key(request.authorization.username, request.authorization.password)
        name = {'user': request.authorization.username}
        # {req_id: {'user': user, 'type': {all: all} / {'nonce': nonce} / {hash: hash}}}
        if text == 'all':           # reads all data in block chain
            get = {'user': user, 'type': 'all'}
            d = {'data': get, 'user': user, 'timestamp': str(datetime.datetime.now())}
            trans_id = get_transaction_id(**d)
            client.publish(f'blockchain/worker/{winner}/read', pickle.dumps({trans_id: get}))
            response = get_response(trans_id)
            if type(response).__name__ == 'list':
                response.append(name)
            return json.dumps(response)
        else:
            try:
                data = ast.literal_eval(text)      # converts data to dictionary
                if type(data).__name__ == 'dict':
                    get = {'user': user, 'type': data}
                    d = {'data': get, 'user': user, 'timestamp': str(datetime.datetime.now())}
                    trans_id = get_transaction_id(**d)
                    client.publish(f'blockchain/worker/{winner}/read', pickle.dumps({trans_id: get}))
                    response = get_response(trans_id)
                    if type(response).__name__ == 'list':
                        response.append(name)
                    return json.dumps(response)         # reads a particular block with nonce id or hash
                else:
                    return json.dumps({'error': 'wrong format -> Example -> {nonce: 1} or {hash_: 127hdwu861eh}'})
            except Exception as e:
                return json.dumps({'error': str(e)})


api.add_resource(HomePage, '/')
api.add_resource(AddBlock, '/add/')
api.add_resource(Read, '/read/<text>')
api.add_resource(Register, '/register/')


class BrokerSend:
    def __init__(self, user, pw, ip, sub_topic, data):
        self.user = user
        self.pw = pw
        self.ip = ip
        self.port = 1883
        self.topic = sub_topic
        self.response = None
        self.client = mqtt.Client()
        self.client.username_pw_set(self.user, self.pw)
        self.client.connect(self.ip, self.port, 60)
        self.data = data

    def publish(self):
        self.client.publish(self.topic, self.data, retain=True)


if __name__ == '__main__':
    h1 = Thread(target=broker_loop)
    h1.start()
    BrokerSend(user=username, pw=password, ip=broker_ip, sub_topic='blockchain/config', data=pickle.dumps(admin)).publish()
    print('admin:', admin)
    app.run(debug=True)
