import streamlit as st
import pandas as pd
import requests
import logging
import ast


class QueryBlockchain:
    def __init__(self, baseURL: str = "http://localhost:8080") -> None:
        self.user_auth = ("jim", "pass")
        self.admin = ("admin", "admin")
        self.baseURL: str = baseURL
        self.register(data={"user": self.user_auth[0], "pw": self.user_auth[1]})

    def get_all(self) -> list:
        endpoint = f"{self.baseURL}/read/all"
        response = requests.get(endpoint, auth=self.admin)
        try:
            data = response.json()
            if type(data).__name__ == "str":
                data = ast.literal_eval(data)
        except Exception as e:
            logging.exception(e)
            data = []

        return data

    def post_data(self, data) -> None:
        endpoint = f"{self.baseURL}/add/"
        response = requests.post(endpoint, json=data, auth=self.user_auth)
        try:
            logging.info(response.json())
        except Exception as e:
            logging.error(
                f"Error with post data ({response.status_code}): {e} = {response.content}"
            )

    def register(self, data) -> None:
        endpoint = f"{self.baseURL}/register/"
        response = requests.post(endpoint, json=data, auth=self.user_auth)
        try:
            logging.info(response.json())
        except Exception as e:
            logging.error(
                f"Error with post data ({response.status_code}): {e} = {response.content}"
            )


def writer(column, chain: QueryBlockchain):
    column.write("# Blockchain Writer")
    column.divider()
    input_type = column.select_slider(
        label="Select input type", options=["json", "text"]
    )

    init_df = pd.DataFrame({"Key": ["add key.."], "Value": ["add value.."]})

    def writer_display():
        if input_type == "json":
            df = column.data_editor(
                init_df, num_rows="dynamic", hide_index=True, use_container_width=True
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
        with st.spinner("Adding new block to chain") as spinner:
            chain.post_data(data=data)
        st.success(body="Block successfully added", icon="✅")


def ledger(column, chain: QueryBlockchain):
    ledger_data = chain.get_all()

    column.write("# Blockchain Ledger")
    column.divider()

    if len(ledger_data) == 0:
        column.write("🚫:red[No data in ledge]🚫")
        return

    block: int = 1
    limit: int = len(ledger_data) - 2
    for data in ledger_data[:-1]:
        column.expander(f"📦 Block {block}").json(data)
        if block <= limit:
            column.write("⬇︎")
        block += 1


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    input_key = 0
    main_column = st
    sidebar = st.sidebar
    blockchain = QueryBlockchain()

    writer(sidebar, blockchain)
    ledger(main_column, blockchain)
