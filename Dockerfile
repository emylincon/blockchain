FROM python:3.8

COPY . .

WORKDIR /blockchain

RUN apt update && apt install -y mosquitto mosquitto-clients && \
    pip install -r requirements

CMD [python]