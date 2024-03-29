from flask import Flask, request, make_response
from flask_restful import Resource, Api
from engine import BlockChain
import ast
import json
from users import Data
from functools import wraps
import config

app = Flask(__name__)
api = Api(app)  # initializing app
store = Data()  # initializing user data
admin = store.get_key(**config.test)  # creating super user
chain = BlockChain(admin)  # initializing block chain


def auth_required(f):
    # user verification authentication
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


class Register(Resource):  # Registration resource
    @staticmethod
    def post():  # user sends a json containing username & password -> {"user": "john", "pw": "pass"}
        try:
            reg_data = request.get_json()
            if set(reg_data.keys()) == {'user', 'pw'}:  # checks if format is followed
                if store.add_item(**reg_data) == 1:
                    return json.dumps({'info': f'registration successful for {reg_data["user"]}'})
                else:
                    return json.dumps({'error': f'Error {reg_data["user"]} already exists'})
            else:
                return json.dumps({'error': 'invalid data sent: format -> {"user": "john", "pw": "pass"}'})
        except AttributeError:
            return json.dumps({'error': 'invalid data sent: format -> {"user": "john", "pw": "pass"}'})


class AddBlock(Resource):
    @staticmethod
    @auth_required
    def post():
        user = store.get_key(request.authorization.username, request.authorization.password)
        sent_data = request.get_json()
        if sent_data != '':
            return chain.add_block(sent_data, user), 201
        else:
            return {'error': 'no data sent'}


class Read(Resource):
    @staticmethod
    @auth_required
    def get(text):
        user = store.get_key(request.authorization.username, request.authorization.password)
        name = {'user': request.authorization.username}
        if text == 'all':  # reads all data in block chain
            response = chain.read_all(user)
            if type(response).__name__ == 'list':
                response.append(name)
            return json.dumps(response)
        else:
            try:
                data = ast.literal_eval(text)  # converts data to dictionary
                if type(data).__name__ == 'dict':
                    response = chain.read_block(**data, user=user)
                    if type(response).__name__ == 'list':
                        response.append(name)
                    return json.dumps(response)  # reads a particular block with nonce id or hash
                else:
                    return json.dumps({'error': 'wrong format -> Example -> {nonce: 1} or {hash_: 127hdwu861eh}'})
            except Exception as e:
                return json.dumps({'error': str(e)})


api.add_resource(HomePage, '/')
api.add_resource(AddBlock, '/add/')
api.add_resource(Read, '/read/<text>')
api.add_resource(Register, '/register/')

if __name__ == '__main__':
    app.run(debug=True)
