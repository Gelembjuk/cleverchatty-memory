import os 
import threading
import time
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request

from app.config import Config
from app.memory import Memory

# Load config
config = Config(os.path.dirname(os.path.realpath(__file__)) + "/.env")

# This will be used in future. Currently not used yet.
auth_token = ""
worker_stop_event = threading.Event()
worker_thread = None  # Will hold our th


def worker():
    """Worker thread to check for new messages and analyse them"""
    while not worker_stop_event.is_set():
        # every 30 seconds go to check ifthere are new messages and analyse them 
        Memory(config).patch_memories_if_new_data()
        time.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_thread

    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()

    yield 

    worker_stop_event.set()
    worker_thread.join()

app = FastAPI(lifespan=lifespan)
mcp = FastMCP("Memory Server")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware to check for the auth token in the header"""
    auth_header = request.headers.get("Authorization")
    if auth_header:
        # extract token from the header and keep it in the global variable
        global auth_token
        auth_token = auth_header.split(" ")[1]
    
    response = await call_next(request)
    
    return response



@mcp.tool()
def remember(role: str, contents) -> str:
    """Remembers new data in the memory"""

    Memory(config).remember(role, contents)

    return "ok"

@mcp.tool()
def recall() -> str:
    """Recall the memory"""
    
    r = Memory(config).recall()

    if not r:
        return "none"
    
    return r

@mcp.tool()
def search_in_memory(data: str) -> str:
    """Searches for data in the memory"""
    
    result = Memory(config).search(data)
    
    if not result:
        return "No results found"
    return result

app.mount("/", mcp.sse_app())