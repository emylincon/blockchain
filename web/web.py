import streamlit as st
import pandas as pd
import requests
import logging
import ast
import os
import json
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env


class QueryBlockchain:
    def __init__(self, baseURL: str = "http://localhost:8080") -> None:
        self.user_auth = ("jim", "pass")
        self.admin = ("admin", "admin")
        self.baseURL: str = baseURL
        self.init()

    def init(self):
        def do():
            code = self.register(
                data={"user": self.user_auth[0], "pw": self.user_auth[1]}
            )
            logging.info(f"register code: {code}")
            if code in [200, 201]:
                st.session_state["register"] = True

        if not st.session_state.get("register"):
            do()

    def get_all(self) -> tuple[list | int]:
        endpoint = f"{self.baseURL}/read/all"
        data = []
        try:
            response = requests.get(endpoint, auth=self.admin)
        except (ConnectionRefusedError, ConnectionError, requests.ConnectionError) as e:
            logging.error(f"connection error: {e}")
            return data, 500

        try:
            data = response.json()
            if type(data).__name__ == "str":
                data = ast.literal_eval(data)
        except Exception as e:
            logging.exception(e)

        return data, response.status_code

    def post_data(self, data) -> int:
        global df_winners
        endpoint = f"{self.baseURL}/add/"
        try:
            response = requests.post(endpoint, json=data, auth=self.user_auth)
        except (ConnectionRefusedError, ConnectionError, requests.ConnectionError) as e:
            logging.error(f"connection error: {e}")
            return 500
        try:
            json_res = response.json()
            logging.info(f"mine_response, {json_res}")
        except Exception as e:
            logging.error(
                f"Error with post data ({response.status_code}): {e} = {response.content}"
            )
        return response.status_code

    def register(self, data) -> int:
        endpoint = f"{self.baseURL}/register/"
        try:
            response = requests.post(endpoint, json=data, auth=self.user_auth)
        except (ConnectionRefusedError, ConnectionError, requests.ConnectionError) as e:
            logging.error(f"connection error: {e}")
            return 500
        try:
            logging.info(response.json())
        except Exception as e:
            logging.error(
                f"Error register ({response.status_code}): {e} = {response.content}"
            )
        return response.status_code

    def times(self):
        endpoint = f"{self.baseURL}/times/"
        data = {}
        try:
            response = requests.get(endpoint, auth=self.user_auth)
        except (ConnectionRefusedError, ConnectionError, requests.ConnectionError) as e:
            logging.error(f"connection error: {e}")
            return self.get_times_column_data(json_data=data), 500
        try:
            json_res = response.json()
            if type(json_res).__name__ == "str":
                json_res = json.loads(json_res)
            logging.info(f"times: {json_res}, {type(json_res)}")
        except Exception as e:
            logging.error(f"times error: {e}")
            return self.get_times_column_data(json_data=data), 500

        return self.get_times_column_data(json_data=json_res), response.status_code

    @staticmethod
    def get_times_column_data(json_data: dict) -> pd.DataFrame:
        default = pd.DataFrame({"Workers": [], "Times": [], "Winner": []})
        if len(json_data) == 0:
            return default
        input_dict = {
            "Workers": list(json_data.keys()),
            "Times": list(json_data.values()),
        }
        logging.info(f"input_dict: {input_dict}")
        df = pd.DataFrame(input_dict)
        try:
            df.sort_values(by="Times", inplace=True)
        except Exception as e:
            logging.error(f"Error sorting times: {e}, {df.to_dict()}")
            return default
        df["Winner"] = ["👑"] + ["😵" for _ in range(df.last_valid_index())]
        return df


def winner_display(column, chain: QueryBlockchain):
    data, code = chain.times()

    logging.info(f"wins: {len(data)}, code: {code}")

    column.write(data)


def writer(column, chain: QueryBlockchain):
    column.write("# Blockchain Writer")
    column.divider()
    input_type = column.select_slider(
        label="Select input type", options=["json", "text"]
    )

    init_df = pd.DataFrame({"Key": ["add key.."], "Value": ["add value.."]})
    table_key = "table"

    def writer_display():
        if input_type == "json":
            df = column.data_editor(
                init_df,
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True,
                key=table_key,
            )
            button = column.button(
                label="Submit", type="primary", help="Add new block to ledger"
            )
            column.write("### Json Preview")
            column.divider()
            keys, values = df.to_dict(orient="list").values()
            data = dict(zip(keys, values))

            column.json(data)

        else:
            data = column.text_area(label="Text Input", placeholder="Enter text..")
            button = column.button(
                label="Submit", type="primary", help="Add new block to ledger"
            )
        return button, data

    button, data = writer_display()
    if button:
        logging.info("posting block to ledger")
        response_code: int = 0
        with st.spinner("Adding new block to chain") as spinner:
            response_code = chain.post_data(data=data)
        if response_code in [200, 201]:
            st.success(body="Block successfully added", icon="✅")
        else:
            st.error(body="Block not added", icon="❌")
        # st.session_state.clear()


def ledger(column, chain: QueryBlockchain):
    ledger_data, status_code = chain.get_all()
    if status_code == 500:
        st.error(body="Could not read from blockchain", icon="❌")

    if len(ledger_data) == 0:
        column.write("🚫:red[No data in ledge]🚫")
        return

    block: int = 1
    limit: int = len(ledger_data) - 2
    for data in ledger_data[:-1]:
        column.expander(f"🗳️ Block {block}").json(data)
        if block <= limit:
            column.write("⬇︎")
        block += 1


if __name__ == "__main__":
    # Page configuration
    st.set_page_config(
        page_title="Blockchain",
        page_icon="🗳️",
        initial_sidebar_state="auto",
        layout="wide",
    )

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    st.write("# Blockchain Ledger")
    st.divider()

    df_winners = pd.DataFrame({"Workers": [], "Times": [], "Winner": []})
    ledger_col, winner_col = st.columns([3, 1])
    # main_column = st
    sidebar = st.sidebar
    blockchain_url: str | None = os.environ.get("BLOCKCHAIN_API")
    if blockchain_url:
        blockchain = QueryBlockchain(baseURL=blockchain_url)
    else:
        logging.error("BLOCKCHAIN_API environment variable is not set")
        blockchain = QueryBlockchain()
    st.write()
    writer(sidebar, blockchain)
    ledger(ledger_col, blockchain)
    winner_display(winner_col, blockchain)
