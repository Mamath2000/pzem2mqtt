FROM python:3-slim-buster

LABEL maintainer="mamath"

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /app
WORKDIR /app/config
VOLUME /app/config

WORKDIR /app

ADD reset.py /app

CMD [ "python3", "/app/reset.py"]
# CMD /bin/sh
