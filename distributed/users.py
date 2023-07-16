import hashlib
import random
import os
import sys
from dotenv import load_dotenv
import logging


class Data:  # this class stores registered user data
    def __init__(self):
        self.data = {}
        load_dotenv()
        self.secret = self.gen_secret
        self.creds = self.__get_creds()
        self.add_item(**self.creds)

    def add_item(self, user, pw):
        key = self.get_key(user, pw)
        if self.verify(key):
            return 0
        else:
            self.data[key] = user
            return 1

    def __get_creds(self) -> dict:
        user = os.getenv("API_ADMIN_USER")
        password = os.getenv("API_ADMIN_USER_PASSWORD")
        if user is None or password is None:
            logging.error("API_ADMIN_USER / API_ADMIN_USER_PASSWORD ENV is not set")
            sys.exit(1)
        return {"user": user, "pw": password}

    def delete_item(self, key):
        del self.data[key]

    def invert_data(self):
        return {v: k for k, v in self.data.items()}

    def verify(self, key):
        if key in self.data:
            return True
        return False

    def get_key(self, user, pw):
        h = hashlib.sha256()
        h.update(
            str(user).encode("utf-8")
            + str(pw).encode("utf-8")
            + str(self.secret).encode("utf-8")
        )
        return h.hexdigest()

    @staticmethod
    def gen_secret():
        return random.randint(111111111111111111111, 1111111111111111111111111111111111)
