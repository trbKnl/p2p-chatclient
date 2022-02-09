### P2P chat application

This repo contains a python `client.py` script that connects to a custom rendezvous server hosted at `rendezvous.niekdeschipper.com`.

#### Installation

Install the dependencies in `requirements.txt`.

```
# use a virtual env install:
python3 -m venv ./env
source env/bin/activate
pip3 install -r requirements.txt
```

#### Usage

`python3 ./client.py`. Enter a string if, someone else connects and puts in the same string, you will be connected through a TCP socket and dumped in a small chat program.


