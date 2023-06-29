import unittest
from blockchain_api import app


class TestApp(unittest.TestCase):
    auth = ("john", "pass")
    sample_data = [
        {
            "nonce": 20408,
            "data": "Genesis",
            "date": "2023-06-25 09:01:56.607131",
            "hash": "0000c9aa0296621f4cc54093923ccd51a67003048dae36aa68a3d2182e6e877f",
            "user": "cbe2cc25d6aed01e31859c4cbb7b793ddd2d6351f86da892d69d4830e598ce2c",
        },
        {
            "nonce": 76624,
            "data": {"name": "emeka"},
            "date": "2023-06-25 09:02:38.231031",
            "hash": "000087b154e58235e15954ddbcb93ca9fff71c6b75741a30f3f7e084d4308f78",
            "user": "0f993d934f68b39482503d51e80fed10c725d5da7e39e9a2002fd4d859bb9d1e",
        },
        {"user": "admin"},
    ]

    @classmethod
    def setUpClass(cls):
        cls.tester = app.test_client(cls)
        # cls.auth = ('john', 'pass')

    def post_data(self, data, endpoint):
        response = self.tester.post(endpoint, json=data)
        return response

    def test_index(self):
        response = self.tester.get("/")
        status_code = response.status_code
        self.assertEqual(status_code, 200)

    def test_register(self):
        response = self.post_data(
            endpoint="/register", data={"user": self.auth[0], "pw": self.auth[1]}
        )
        status_code = response.status_code
        self.assertEqual(status_code, 308)

    def test_add(self):
        data = {"temp": 20, "hum": 55, "time": "11:00"}
        response = self.post_data(endpoint="/add", data=data)
        status_code = response.status_code
        self.assertEqual(status_code, 308)

    def test_read(self):
        response = self.tester.get("read/all")
        status_code = response.status_code
        self.assertEqual(status_code, 200)


if __name__ == "__main__":
    unittest.main()
