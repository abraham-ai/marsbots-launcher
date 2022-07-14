import io
import json
import os
import zipfile
from dataclasses import dataclass

from fastapi import Depends
from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from .const import BOT_DIR
from .const import ROOT_DIR


@dataclass
class KeyPair:
    uid: str
    token: str


def get_keypair():
    with open(os.path.join(ROOT_DIR, "credential.json"), "r") as f:
        return KeyPair(**json.load(f))


KEYPAIR = get_keypair()
DATABASE_URL = "postgresql://marsbots:marsbots@db:5432/marsbots"


def check_token(bearer_auth):
    if bearer_auth != KEYPAIR.token:
        raise Exception("Invalid token")


def get_user_token(
    res: Response,
    credential: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is needed",
            headers={"WWW-Authenticate": 'Bearer realm="auth_required"'},
        )
    try:
        check_token(credential.credentials)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication from Firebase. {err}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    res.headers["WWW-Authenticate"] = 'Bearer realm="auth_required"'
    return {}


app = FastAPI()

origins = ["http://localhost:3000", "localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


class TestRequest(BaseModel):
    user: dict = Depends(get_user_token)


@app.get("/user_token")
async def hello_user(user: dict = Depends(get_user_token)):
    return {"msg": "Hello, user", "uid": "wow"}


@app.post("/deploy")
async def deploy(
    bot_name: str = Form(),
    bot_code: UploadFile = File(...),
    user: dict = Depends(get_user_token),
):
    # TODO: get zip file sent by request
    tmp = await bot_code.read()

    with zipfile.ZipFile(io.BytesIO(tmp), "r") as z:
        target_dir = BOT_DIR / bot_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in z.namelist():
            z.extract(name, target_dir)

    return {"Hello": "World"}


class StartBotRequest(BaseModel):
    bot_name: str


@app.post("/start")
def start_bot(req: StartBotRequest, user: dict = Depends(get_user_token)):
    bot_name = req.bot_name
    os.system(
        f"""pm2 start bot.py --name "{bot_name}" -- bots/{bot_name}/{bot_name}.json --cog-path=bots.{bot_name}.{bot_name} --dotenv-path=bots/{bot_name}/.env""",
    )
    return {"Hello": "World"}


class StopBotRequest(BaseModel):
    bot_name: str


@app.post("/stop")
def stop_bot(req: StopBotRequest, user: dict = Depends(get_user_token)):
    bot_name = req.bot_name
    os.system(f"pm2 stop {bot_name}")
    return {"Hello": "World"}
