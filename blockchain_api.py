from flask import Flask, request, make_response
from flask_restful import Resource, Api
from engine import BlockChain
import ast
import json
from users import Data
from functools import wraps


app = Flask(__name__)
api = Api(app)                # initializing app
chain = BlockChain()          # initializing block chain
store = Data()                # initializing user data


def auth_required(f):
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
        return {'about': 'Welcome to Emeka\'s implementation of blockchain!'}


class Register(Resource):
    @staticmethod
    def post():
        try:
            reg_data = request.get_json()
            if set(reg_data.keys()) == {'user', 'pw'}:
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
        sent_data = request.get_json()
        if sent_data != '':
            return chain.add_block(sent_data), 201
        else:
            return {'error': 'no data sent'}


class Read(Resource):
    @staticmethod
    @auth_required
    def get(text):
        if text == 'all':
            return json.dumps(chain.read_all())
        else:
            try:
                data = ast.literal_eval(text)
                if type(data).__name__ == 'dict':
                    a = chain.read_block(**data)
                    return json.dumps(a)
                else:
                    return {'error': 'wrong format -> Example -> {nonce: 1} or {hash_: 127hdwu861eh}'}
            except Exception as e:
                return {'error': e}


api.add_resource(HomePage, '/')
api.add_resource(AddBlock, '/add/')
api.add_resource(Read, '/read/<text>')
api.add_resource(Register, '/register/')


if __name__ == '__main__':
    app.run(debug=True)
