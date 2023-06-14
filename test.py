import paho.mqtt.client as mqtt
import time


class BrokerSend:
    def __init__(
        self, data, user="admin", pw="password", ip="localhost", sub_topic="light"
    ):
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


# b = BrokerSend(data="light on", ip="broker")
# b.publish()
# print("message received")
while True:
    time.sleep(1)
