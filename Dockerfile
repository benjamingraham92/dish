FROM debian:trixie-slim

RUN \
    apt update && \
    apt upgrade -y && \
    apt install -y \
        locales \
        python3 \
        python3-dev \
        python3-venv && \
    rm -rf /var/lib/apt/lists/* && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

ENV LANG en_US.utf8

COPY app /app

RUN python3 -m venv opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /

RUN \
    python -m ensurepip --upgrade && \
    pip install --upgrade setuptools && \
    pip install -r requirements.txt

WORKDIR /app

CMD python3 webscraper.py
