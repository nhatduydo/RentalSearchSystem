import asyncio

import websockets


async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/test/"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            await websocket.send("Hello, WebSocket!")
            response = await websocket.recv()
            print(f"Received: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
