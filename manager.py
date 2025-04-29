import typer
import os 
import sys
application_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(application_path)

from app.config import Config
from app.config import Config
from app.memory import Memory

"""
This is a command line interface for the memory server.
It allows to manage the memory from the command line.
It is used for "debug" and "test" purposes.
"""

# Load config
application_path = os.path.dirname(os.path.realpath(__file__))
config = Config(application_path + "/.env")

app = typer.Typer()

@app.command()
def remember(role: str, contents: str):
    """Remembers new data in the memory"""

    Memory(config).remember(role, contents)

    print("ok")

@app.command()
def recall():
    """Recall the memory"""
    
    r = Memory(config).recall()

    if not r:
        print("none")
        return

    print(r)

@app.command()
def history_dump():
    """Dumps the history of the memory"""
    
    gen = Memory(config).history_dump()

    print("Hostory:")
    for i in gen:
        print(i)

@app.command()
def search_in_memory(data: str):
    """Searches for data in the memory"""
    
    r = Memory(config).search(data)

    if not r:
        print("none")
        return

    print(r)

@app.command()
def clear_memory():
    """Clears the memory"""
    
    Memory(config).clear()

    print("ok")

@app.command()
def patch_memories():
    """Patches the memories"""
    
    result_log = Memory(config).patch_memories()

    print(result_log)

@app.command()
def rebuild_memories():
    """Rebuilds the memories"""
    
    result_log = Memory(config).rebuild_memories()

    print(result_log)

if __name__ == "__main__":
    app()