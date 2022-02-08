
import sys
import socket
import asyncio
import aioconsole



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


async def start_chat(sock: socket.socket) -> None:
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


