#!/bin/sh
nohup redis-server &
python3 ./gather.py
