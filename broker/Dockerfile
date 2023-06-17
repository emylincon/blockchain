FROM ubuntu:20.04

EXPOSE 1883

WORKDIR /broker

COPY start.sh .

RUN apt update && apt install mosquitto mosquitto-clients netcat -y && \
    chmod +x start.sh

CMD ["./start.sh"]