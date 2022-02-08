import asyncio
import websockets
import uuid
import aioredis
import random

TIMEOUT = 300

class WebsocketConnectionError(Exception):
    pass


async def is_websock_alive(websock) -> None:
    try:
        await websock.recv()
    except websockets.exceptions.ConnectionClosed as e:
        raise WebsocketConnectionError(e) from e


async def session_handshake(connstring: str, my_sessionid: str, websocket) -> str:
    r = aioredis.Redis.from_url("redis://localhost", decode_responses=True)

    has_val = await r.llen(connstring)
    # peer has already connected to the rendezvous server 
    if has_val == 1:
        other_sessionid = await r.lpop(connstring)
        await r.lpush(other_sessionid, my_sessionid)
    # if not you are the first to connect to the rendezvous server
    else :
        await r.lpush(connstring, my_sessionid)

        # while waiting on peer to connect keep checking if websocket is alive
        task1 = asyncio.create_task(r.blpop(my_sessionid, timeout=TIMEOUT), name="waiting_for_peer_to_connect")
        task2 = asyncio.create_task(is_websock_alive(websocket), name="check_if_websocket_is_alive")
        
        # done and pending should be awaited
        done, pending = await asyncio.wait(
                {task1, task2},
                return_when=asyncio.FIRST_COMPLETED
        )

        # if handshake was succesfull return other_sessionid
        # otherwise close websocket, in any case entries in redis should be deleted
        try:
            for task in done:
                _, other_sessionid = await task
        except WebsocketConnectionError as e:
            print("client got disconnected")
            await websocket.close()
            raise e
        finally:
            for task in pending:
                print(f"task: {task.get_name()} will be canceled")
                task.cancel()
            await r.delete(connstring, my_sessionid)

    return other_sessionid


async def push_my_session_info(websocket, other_sessionid: str) -> None:
    r = aioredis.Redis.from_url("redis://localhost", decode_responses=True)

    my_session_info = await websocket.recv()
    await r.lpush(other_sessionid, my_session_info)



async def pop_other_session_info(my_sessionid: str) -> str:
    r = aioredis.Redis.from_url("redis://localhost", decode_responses=True)

    other_session_info = None
    if await r.llen(my_sessionid) != 0:
        other_session_info = await r.lpop(my_sessionid)
    else:
        _, other_session_info = await r.blpop(my_sessionid, timeout=TIMEOUT)
    return other_session_info


async def main_exchange(websocket, path):

    print("Client connected to server")
    my_sessionid = str(uuid.uuid1())
    print(f"Your session id is: {my_sessionid}")

    await websocket.send("Connected to rendezvous server")

    # wait for a connection string
    connstring = await websocket.recv()

    # wait for another client with the same connection string
    # exchange sessionid numbers
    try:
        other_sessionid = await session_handshake(connstring, my_sessionid, websocket)
    except WebsocketConnectionError as e:
        return

    # start IP and PORT exchange
    await websocket.send("Peer connected, starting IP and PORT exchange...")
    _, other_session_info = await asyncio.gather(
            push_my_session_info(websocket, other_sessionid),
            pop_other_session_info(my_sessionid)
    )
    await websocket.send(other_session_info)
    print("Exchange succesfull")


async def main():
    async with websockets.serve(main_exchange, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())


