import os

topics = ['blockchain/worker/chain', 'blockchain/worker/mine', 'blockchain/worker/add', 'blockchain/worker/times',
          'blockchain/api/block_winner', 'blockchain/api/notification']

for topic in topics:
    cmd = f"mosquitto_pub -h 192.168.40.178 -t {topic} -u admin -P password -n -r -d"
    os.system(cmd)


print('All topics have been reset')
