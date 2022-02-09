import sys
import socket
import queue
import threading
import time

import logging

HOST = '0.0.0.0'
SOCKET_TO_USE = queue.Queue()
LOGGER = logging.getLogger(__name__)

def pick_open_port() -> int:
    sock = socket.socket()
    sock.bind(('', 0))
    port  = sock.getsockname()[1]
    sock.close()
    LOGGER.debug("Picked port: %s", port)
    return port


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
            SOCKET_TO_USE.put(conn)
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
            SOCKET_TO_USE.put(sock)
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
    t1.start()
    t2.start()

    sock_out = SOCKET_TO_USE.get()
    return sock_out



