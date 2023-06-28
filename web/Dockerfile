FROM python:3.10

WORKDIR /web

EXPOSE 8501

COPY . .

RUN apt update && apt install -y curl && \
    pip install -r requirements.txt

ENTRYPOINT [ "streamlit", "run", "web.py" ]

CMD [ "--server.headless=true", "--server.runOnSave=false", "--server.port=8501", "--browser.gatherUsageStats=false", "--client.showErrorDetails=false" ]
