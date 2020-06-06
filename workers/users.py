import hashlib
import random
import config


class Data:             # this class stores registered user data
    def __init__(self):
        self.data = {}
        self.secret = self.gen_secret
        self.add_admin(**config.test)        # adds admin user for testing

    def add_item(self, user, pw):
        key = self.get_key(user, pw)
        if self.verify(key):
            return 0
        else:
            self.data[key] = user
            return 1

    def delete_item(self, key):
        del self.data[key]

    def add_admin(self, user, pw):
        secret = '1201iodmpdocm2qpd;ocjm'
        h = hashlib.sha256()
        h.update(
            str(user).encode('utf-8') +
            str(pw).encode('utf-8') +
            str(secret).encode('utf-8')
        )
        key = h.hexdigest()
        if not self.verify(key):
            self.data[key] = user

    def invert_data(self):
        return {v: k for k, v in self.data.items()}

    def verify(self, key):
        if key in self.data:
            return True
        return False

    def get_key(self, user, pw):
        h = hashlib.sha256()
        h.update(
            str(user).encode('utf-8') +
            str(pw).encode('utf-8') +
            str(self.secret).encode('utf-8')
        )
        return h.hexdigest()

    @staticmethod
    def gen_secret():
        return random.randint(111111111111111111111, 1111111111111111111111111111111111)

