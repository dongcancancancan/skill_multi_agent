from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .agents import router as agents_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Multi-Agent Financial Assistant API",
    description="API endpoints for interacting with financial agents",
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_methods=["POST"])


app.include_router(agents_router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        pass
