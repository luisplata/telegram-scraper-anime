FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get upgrade -y && apt-get dist-upgrade -y && \
    apt-get install -y --no-install-recommends gcc libffi-dev libssl-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc libffi-dev libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["bash", "-c", "while true; do python3 anime_main.py ${DIAS}; sleep 86400; done"]
