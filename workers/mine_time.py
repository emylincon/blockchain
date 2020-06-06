import hashlib, pickle, datetime

difficulty = 4
difficulty_string = ''.join(['0' for x in range(difficulty) ])


top_block = {'nonce': 1, 'data': {'transaction 1': '$100'}, 'date': str(datetime.datetime.now())}

p = hashlib.sha3_256()
a = datetime.datetime.now()
while True:
    if p.hexdigest()[:difficulty] == difficulty_string:
        top_block['hash'] = p.hexdigest()
        print(f'time: {datetime.datetime.now() - a}')
        break
    else:
        top_block['nonce'] += 1
        p.update(pickle.dumps(top_block) )
        print(top_block)
print(top_block)