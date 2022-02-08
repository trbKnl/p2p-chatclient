#!/usr/bin/env python

import asyncio
import json
import websockets
import stun
import logging
from helpers import chat
from helpers import holepunch


logging.basicConfig(format='%(asctime)s - %(name)s -  %(levelname)s - %(message)s')

my_modules = ["helpers.holepunch"]
for m in my_modules:
    logging.getLogger(m).setLevel(logging.DEBUG)


import os,sys,stat

async def get_my_ip_info() -> dict:
    nat_type, external_ip, _ = stun.get_ip_info(stun_host='192.168.2.8')
    srcport = holepunch.pick_open_port()
    print(srcport)
    out = {
            "nat_type" : nat_type,
            "external_ip" : external_ip,
            "external_port" : srcport
        }
    return out


async def connect_to_rendezvous_server(uri: str) -> (dict, dict):
    async with websockets.connect(uri) as websocket:
        try:
            print("isatty():", sys.stdin.isatty())
            print("isfifo():", stat.S_ISFIFO(os.fstat(0).st_mode))
            sys.stdin = open("/dev/tty")

            # when connected to the server receive a greeting
            greeting = await websocket.recv()
            print(greeting)

            # ask the user to put in a connection string
            # you get connected to a user that put in the same string
            connstring = input("Input a connection string: ")
            await websocket.send(connstring)
            status = await websocket.recv()
            print(status)

            # If someone else connected with the same connstring
            # obtain info from stun server and send to the rendezvous server
            my_ip_info = await get_my_ip_info()
            my_ip_info_json = json.dumps(my_ip_info)
            await websocket.send(my_ip_info_json)

            # obtain connection info on peer from rendezvous server
            other_ip_info_json = await websocket.recv()
            other_ip_info = json.loads(other_ip_info_json)

            return (my_ip_info, other_ip_info)
        except KeyboardInterrupt:
            websocket.close()



async def main() -> None:
    my_ip_info, other_ip_info = await connect_to_rendezvous_server("ws://192.168.2.8:8765")
    print(my_ip_info)
    print(other_ip_info)

    try:
        socket = holepunch.create_socket(
            dsthost = other_ip_info['external_ip'],
            dstport = other_ip_info['external_port'],
            srcport = my_ip_info['external_port']
        )
    except KeyboardInterrupt:
        return

    await chat.start_chat(socket)


try :
    asyncio.run(main())
except KeyboardInterrupt:
    pass



