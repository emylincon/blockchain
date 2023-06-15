FROM python:3.8

WORKDIR /blockchain

EXPOSE 5000

COPY . .

RUN apt update && apt install -y mosquitto mosquitto-clients curl && \
    pip install -r requirements.txt

ENTRYPOINT [ "python" ]

CMD ["workers/distributed_api.py"]