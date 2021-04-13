FROM python:3.8-alpine

RUN adduser -D cms

WORKDIR /home/cms


COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN apk --update add libxml2-dev libxslt-dev libffi-dev gcc musl-dev libgcc openssl-dev curl
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql

COPY app app
COPY migrations migrations
COPY cms.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP cms.py

RUN chown -R cms:cms ./
USER cms

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]