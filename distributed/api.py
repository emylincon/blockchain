from flask import Flask, request, make_response
from flask_restful import Resource, Api
import ast
import json
from users import Data
from functools import wraps
import pickle
import paho.mqtt.client as mqtt
import hashlib
import datetime
from threading import Thread
import os
import sys
import logging
from dotenv import load_dotenv


def on_connect(connect_client, userdata, flags, rc):
    print("Connected with Code :" + str(rc))
    # Subscribe Topic from here
    connect_client.subscribe(topic)


# Callback Function on Receiving the Subscribed Topic/Message
def on_message(message_client, userdata, msg):
    global winner

    # print the message received from the subscribed topic
    print("top: ", msg.topic)
    topic_recv = msg.topic.split("/")[-1]
    print("topic received:", topic_recv)
    if topic_recv == "block_winner":
        winners = pickle.loads(msg.payload)
        print(f"winners: {winners} \nWinner: {winners[-1]}")
        winner = winners[-1]

    elif topic_recv == "notification":
        notify.update(pickle.loads(msg.payload))
        print(notify)


def broker_loop():
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set(username, password)
    client.connect(broker_ip, broker_port_no, 60)
    client.loop_forever()


def auth_required(f):  # user verification authentication
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        try:
            if auth:
                if store.verify(store.get_key(auth.username, auth.password)):
                    return f(*args, **kwargs)
                else:
                    return json.dumps({"error": "could not verify login"})
            else:
                return json.dumps({"error": "authentication was not parsed"})
        except Exception as e:
            print("login error", e)
            return json.dumps({"error": "error during login", "e": str(e)})

    return decorated


class HomePage(Resource):
    @staticmethod
    def get():
        return {
            "about": "Welcome to Emeka's implementation of blockchain! To Register use endpoint=> register/"
        }


class Register(Resource):  # Registration resource
    @staticmethod
    # user sends a json containing username & password -> {"user": "john", "pw": "pass"}
    def post():
        try:
            reg_data = request.get_json()
            # checks if format is followed
            if set(reg_data.keys()) == {"user", "pw"}:
                if store.add_item(**reg_data) == 1:
                    return json.dumps(
                        {"info": f'registration successful for {reg_data["user"]}'}
                    )
                else:
                    return json.dumps(
                        {"error": f'Error {reg_data["user"]} already exists'}
                    )
            else:
                return json.dumps(
                    {
                        "error": 'invalid data sent: format -> {"user": "john", "pw": "pass"}'
                    }
                )
        except AttributeError:
            return json.dumps(
                {"error": 'invalid data sent: format -> {"user": "john", "pw": "pass"}'}
            )


class AddBlock(Resource):
    @staticmethod
    @auth_required
    def post():
        global times
        user = store.get_key(
            request.authorization.username, request.authorization.password
        )
        sent_data = request.get_json()
        if sent_data != "":
            mine = {
                "data": sent_data,
                "user": user,
                "timestamp": datetime.datetime.now(),
            }
            trans_id = Util.get_transaction_id(**mine)
            pub = {trans_id: mine}
            client.publish("blockchain/worker/mine", pickle.dumps(pub))
            print(f"published: {pub}")
            try:
                response = Util.get_response(trans_id)
                print(f"times: {response}, type: {type(response)}")
                times_data = response.get("times")
                if times_data:
                    times = times_data
                return json.dumps(response)
            except TypeError:
                return json.dumps(
                    {"error": "json.dumps(get_response(trans_id)) raised a type error"}
                )
        else:
            return json.dumps({"error": "no data sent"})


class Util:
    @staticmethod
    def get_creds() -> dict:
        user = os.getenv("API_ADMIN_USER")
        password = os.getenv("API_ADMIN_USER_PASSWORD")
        if user is None or password is None:
            logging.error("API_ADMIN_USER / API_ADMIN_USER_PASSWORD ENV is not set")
            sys.exit(1)
        return {"user": user, "pw": password}

    @staticmethod
    def get_response(trans_id):
        while True:
            if trans_id in notify:
                response = notify[trans_id]
                del notify[trans_id]
                return response

    @staticmethod
    def get_transaction_id(data, user, timestamp):
        h = hashlib.sha256()
        h.update(
            str(data).encode("utf-8")
            + str(user).encode("utf-8")
            + str(timestamp).encode("utf-8")
        )

        return h.hexdigest()


class Read(Resource):
    @staticmethod
    @auth_required
    def get(text):
        user = store.get_key(
            request.authorization.username, request.authorization.password
        )
        name = {"user": request.authorization.username}
        # {req_id: {'user': user, 'type': {all: all} / {'nonce': nonce} / {hash: hash}}}
        if text == "all":  # reads all data in block chain
            get = {"user": user, "type": "all"}
            d = {"data": get, "user": user, "timestamp": str(datetime.datetime.now())}
            trans_id = Util.get_transaction_id(**d)
            client.publish(
                f"blockchain/worker/{winner}/read", pickle.dumps({trans_id: get})
            )
            print(f"read resquest sent: {d}")
            response = Util.get_response(trans_id)
            if type(response).__name__ == "list":
                for da in response:
                    da["date"] = str(da["date"])
                response.append(name)
            return json.dumps(response)
        else:
            try:
                # converts data to dictionary
                data = ast.literal_eval(text)
                if type(data).__name__ == "dict":
                    get = {"user": user, "type": data}
                    d = {
                        "data": get,
                        "user": user,
                        "timestamp": str(datetime.datetime.now()),
                    }
                    trans_id = Util.get_transaction_id(**d)
                    client.publish(
                        f"blockchain/worker/{winner}/read",
                        pickle.dumps({trans_id: get}),
                    )
                    print(f"read resquest sent: {d}")
                    response = Util.get_response(trans_id)
                    if type(response).__name__ == "list":
                        for da in response:
                            da["date"] = str(da["date"])
                        response.append(name)
                    # reads a particular block with nonce id or hash
                    return json.dumps(response)
                else:
                    return json.dumps(
                        {
                            "error": "wrong format -> Example -> {nonce: 1} or {hash_: 127hdwu861eh}"
                        }
                    )
            except Exception as e:
                return json.dumps({"error": str(e)})


class Times(Resource):
    @staticmethod
    @auth_required
    def get():
        return json.dumps(times)


class BrokerSend:
    def __init__(self, user, pw, ip, sub_topic, data):
        self.user = user
        self.pw = pw
        self.ip = ip
        self.port = 1883
        self.topic = sub_topic
        self.response = None
        self.client = mqtt.Client()
        # self.client.username_pw_set(self.user, self.pw)
        self.client.connect(self.ip, self.port, 60)
        self.data = data

    def publish(self):
        self.client.publish(self.topic, self.data, retain=True)

    def __del__(self):
        print("BrokerSend Object Deleted!")


if __name__ == "__main__":
    print("-----------------------------------")
    print("        BLOCK CHAIN JSON API       ")
    print("-----------------------------------")

    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    # Set up GLOBAL variables
    load_dotenv()  # take environment variables from .env
    username = os.getenv("BROKER_USERNAME")
    password = os.getenv("BROKER_PASSWORD")
    broker_ip = os.getenv("BROKER_IP")
    broker_port_no = int(os.getenv("BROKER_PORT"))
    topic = "blockchain/api/#"
    store = Data()  # initializing user data
    admin = store.get_key(**Util.get_creds())  # creating super user
    winner = ""
    notify = {}  # id : data
    client = mqtt.Client()
    times = {}

    # Flask API set up
    app = Flask(__name__)
    api = Api(app)  # initializing app
    api.add_resource(HomePage, "/")
    api.add_resource(AddBlock, "/add/")
    api.add_resource(Read, "/read/<text>")
    api.add_resource(Register, "/register/")
    api.add_resource(Times, "/times/")

    # Start threads
    h1 = Thread(target=broker_loop)
    h1.start()
    bs = BrokerSend(
        user=username,
        pw=password,
        ip=broker_ip,
        sub_topic="blockchain/config",
        data=pickle.dumps(admin),
    )
    bs.publish()
    del bs
    app.run(debug=True, port=8080, host="0.0.0.0")
