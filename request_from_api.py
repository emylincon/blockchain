import requests
import json
import config
import ast

url = 'http://127.0.0.1:5000/'
auth = ('username', 'password')
auth1 = ('john', 'pass')


def get_data(endpoint='', auth_=None):
    response = requests.get(url + endpoint, auth=auth_, )
    try:
        data = json.loads(response.content)
    except Exception as e:
        data = response.content

    print(data)
    return data


def post_data(data, auth_=None, endpoint=''):
    # response = requests.post(url+endpoint, data='mama', json=data)
    response = requests.post(url + endpoint, json=data, auth=auth_, )
    try:
        d = json.loads(response.content)
    except Exception as e:
        d = response.content
    print(d)
    return d


post_data(endpoint='register/', data={"user": "john", "pw": "pass"})
res = post_data(endpoint='add/', data={'name': 'emeka'}, auth_=auth1)
print('type', type(res))
if type(res).__name__ == 'str':
    res = ast.literal_eval(res)
req1 = {"nonce": res["nonce"]}
get_data(endpoint=f'read/{req1}', auth_=auth1)
req2 = {"hash_": res["hash"]}
get_data(endpoint=f'read/{req2}', auth_=auth1)
get_data(endpoint='read/all', auth_=auth1)
get_data(endpoint='read/all', auth_=config.t)
# get_data()

