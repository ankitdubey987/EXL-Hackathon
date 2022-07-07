FROM python:3.9-alpine3.16

LABEL MAINTAINER="Ankit Kumar Dubey dubey7816@gmail.com"

ENV GROUP_ID=1000 \
    USER_ID=1000

WORKDIR /var/www/

ADD ./requirements.txt /var/www/requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /var/www/
RUN pip install gunicorn

RUN addgroup -g $GROUP_ID www
RUN adduser -D -u $USER_ID -G www www -s /bin/sh

USER www

EXPOSE 5000

# CMD [ "gunicorn", "-w", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]
CMD ["python","app.py"]