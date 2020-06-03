import requests
import json

url = 'http://127.0.0.1:5000/'
auth = ('username', 'password')
auth1 = ('john', 'pass')


def get_data(endpoint='', auth_=None):
    response = requests.get(url + endpoint, auth=auth_, )
    data = json.loads(response.content)
    print(data)


def post_data(data, auth_=None, endpoint=''):
    # response = requests.post(url+endpoint, data='mama', json=data)
    response = requests.post(url + endpoint, json=data, auth=auth_,)
    data = json.loads(response.content)
    print(data)


# post_data(endpoint='register/', data={"user": "john", "pw": "pass"})
# # post_data(endpoint='add/', data={'name': 'emeka'}, auth_=auth1)
# get_data(endpoint='read/{"nonce": 2}', auth_=auth1)
# get_data(endpoint='read/all', auth_=auth1)

