import sys
import socket
import ssl
import asyncio
import time
import argparse
import aioconsole

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(
    certfile='./cert.pem',
    keyfile='./key.pem',
    password="protec"
)

# Generate a self signed certificate
# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
# password: protec

def create_socket(server_mode: bool) -> socket.socket:
    sock_out = None

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    if server_mode:
        sock.bind((HOST, PORT))
        sock.listen()
        print("Listening and accepting connections")
        conn, _ = sock.accept()
        print("Connected to peer")
        sock.close()
        conn.setblocking(False)
        sock_out = conn
    else:
        while True:
            try:
                sock.connect((HOST, PORT))
                break
            except ConnectionRefusedError:
                time.sleep(1)
        print("Connected to peer")
        sock.setblocking(False)
        sock_out = sock
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



def initiate_chat(server_mode: bool) -> None:
    try:
        conn = create_socket(server_mode)
    except KeyboardInterrupt:
        return
    try:
        asyncio.run(start_conversation(conn))
    except KeyboardInterrupt:
        conn.close()
        print()
        print("Connection closed")
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initiate a chat conversation over a TCP socket')
    parser.add_argument('-l',
            action='store_true',
            help="""
            If specified you will be the server
            creating the TCP socket and listening for an incomming connection
            """
    )
    args = parser.parse_args()
    initiate_chat(args.l)



