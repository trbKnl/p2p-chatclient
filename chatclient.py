#!/usr/bin/env python

import sys
import socket
import ssl
import asyncio
import time
import queue
import threading
import aioconsole


HOST = '0.0.0.0'

my_queue = queue.Queue()

def accept(srcport: int, threads_running: threading.Event) -> None:
    print("accept thread started")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, srcport))
    sock.listen()
    sock.settimeout(5)

    while threads_running.is_set():
        try:
            conn, _ = sock.accept()
            threads_running.clear()
            conn.setblocking(False)
            my_queue.put(conn)
            print("connected to peer: as server")
        except socket.timeout:
            print("accept timeout")

    sock.close()
    print("accept thread closed")


def connect(dsthost: str, dstport: int, srcport: int, threads_running: threading.Event) -> None:
    print("connect thread started")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #sock.bind(HOST)
    sock.bind((HOST, srcport))
    sock.settimeout(5)
    while threads_running.is_set():
        try:
            sock.connect((dsthost, dstport))
            threads_running.clear()
            sock.setblocking(False)
            my_queue.put(sock)
            print("connected to peer: as client")
        except socket.error: 
            print("connect timeout")
            time.sleep(1)

    print("connect thread closed")


def create_socket(dsthost: str, dstport: int, srcport: int) -> socket.socket:

    threads_running = threading.Event()
    threads_running.set()
    t1 = threading.Thread(target=accept, args=(srcport, threads_running,))
    t2 = threading.Thread(target=connect, args=(dsthost, dstport, srcport, threads_running,))
    #t1.start()
    t2.start()

    sock_out = my_queue.get()
    return sock_out


async def receiver(sock: socket.socket) -> None:
    while True:
        try :
            msg = sock.recv(1024)
            msg = msg.decode("utf-8")
            if msg != '':
                print("<other> " + msg)
            else:
                raise ConnectionError
        except BlockingIOError:
            pass
        await asyncio.sleep(0.1)


async def sender(sock: socket.socket) -> None:
    while True:
        msg = await aioconsole.ainput()
        msg = bytes(msg.encode())
        sock.send(msg)
        await asyncio.sleep(0.1)


async def start_conversation(sock: socket.socket) -> None:
    sender_task = asyncio.create_task(sender(sock))
    receiver_task = asyncio.create_task(receiver(sock))
    try:
        await asyncio.gather(
            sender_task,
            receiver_task
        )
    except ConnectionError:
        sender_task.cancel()
        receiver_task.cancel()
        sock.close()
        print("Peer closed connection")
        print("Connection closed")


async def initiate_chat(dsthost : str, dstport : int, srcport: int) -> None:
    try:
        conn = create_socket(dsthost, dstport, srcport)
    except KeyboardInterrupt:
        return

    try:
        await start_conversation(conn)
    except KeyboardInterrupt:
        conn.close()
        print()
        print("Connection closed")
    return



async def main():

    my_ip_info = {
            "external_port" : 46787,
    }
    other_ip_info = {
            "external_ip" : "192.168.111.101",
            "external_port" : 26234
    }

    await initiate_chat(
            dsthost = other_ip_info['external_ip'],
            dstport = other_ip_info['external_port'],
            srcport = my_ip_info['external_port']
    )


try :
    asyncio.run(main())
except KeyboardInterrupt:
    pass




