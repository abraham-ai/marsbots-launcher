import os

from const import BOT_DIR
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/deploy")
def deploy(name: str):
    BOT_DIR.mkdir(exist_ok=True)


@app.post("/start")
def start_bot(name: str):
    os.system(
        f"""pm2 start bot.py --name "{name}" -- bots/{name}/{name}.json --cog-path=bots.{name}.{name} --dotenv-path=bots/{name}/.env""",
    )
    return {"Hello": "World"}


@app.post("/stop")
def stop_bot(name: str):
    os.system(f"pm2 stop {name}")
    return {"Hello": "World"}
