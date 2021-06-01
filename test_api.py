import unittest
from blockchain_api import app


class TestApp(unittest.TestCase):
    auth = ('john', 'pass')

    @classmethod
    def setUpClass(cls):
        cls.tester = app.test_client(cls)
        # cls.auth = ('john', 'pass')

    def post_data(self, data, endpoint):
        response = self.tester.post(endpoint, json=data)
        return response

    def test_index(self):
        response = self.tester.get('/')
        status_code = response.status_code
        self.assertEqual(status_code, 200)

    def test_register(self):
        response = self.post_data(endpoint='/register', data={"user": self.auth[0], "pw": self.auth[1]})
        status_code = response.status_code
        self.assertEqual(status_code, 308)

    def test_add(self):
        data = {"temp": 20, "hum": 55, "time": "11:00"}
        response = self.post_data(endpoint='/add', data=data)
        status_code = response.status_code
        self.assertEqual(status_code, 308)

    def test_read(self):
        response = self.tester.get('read/all')
        status_code = response.status_code
        self.assertEqual(status_code, 200)


if __name__ == '__main__':
    unittest.main()