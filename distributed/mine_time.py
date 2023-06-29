import hashlib, pickle, datetime


def mine_block(difficulty=4):
    difficulty_string = ''.join(['0' for x in range(difficulty) ])
    top_block = {'nonce': 1, 'data': {'transaction 1': '$100'}, 'date': str(datetime.datetime.now())}

    p = hashlib.sha3_256()
    a = datetime.datetime.now()
    while True:
        if p.hexdigest()[:difficulty] == difficulty_string:
            top_block['hash'] = p.hexdigest()
            mine_time = datetime.datetime.now() - a
            print(f'diff: {difficulty}, time: {mine_time}')
            break
        else:
            top_block['nonce'] += 1
            p.update(pickle.dumps(top_block) )
            # print(top_block)
    return mine_time
    # print(top_block)


def experiment():
    x = list(range(4,11))
    y = [mine_block(i) for i in x]
    print(dict(zip(x,y)))


if __name__ == '__main__':
    experiment()
