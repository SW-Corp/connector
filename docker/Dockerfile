FROM python:3.9
COPY . /connector
WORKDIR /connector

RUN mkdir "/connector/venv" && python3 -m venv "/connector/venv"

ENV PATH="/connector/venv/bin"

RUN pip install -U pip && pip install -e .

ENTRYPOINT ["connector", "-c", "src/connector/config.conf"]