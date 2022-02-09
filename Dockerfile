FROM arm32v7/alpine:latest

# qemu
COPY qemu-arm-static /usr/bin/

# install redis / pyhon needed packages
RUN apk --update add redis \
    python3\
    py3-pip

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# command in this order for efficient caching Docker
COPY . /app
WORKDIR /app

EXPOSE 8765
CMD ["./start.sh"]
