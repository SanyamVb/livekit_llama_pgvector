FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

ENV HTTP_PROXY="http://EDESM:Sa7a7a4f51*@10.86.255.70:8080"

ENV HTTPS_PROXY="http://EDESM:Sa7a7a4f51*@10.86.255.70:8080"

RUN pip install pip --upgrade

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD 