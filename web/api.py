import os
import zipfile

import boto3
from dotenv import load_dotenv
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import initialize_app
from pydantic import BaseModel

from .const import BOT_DIR
from .const import ROOT_DIR

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

credential = credentials.Certificate(ROOT_DIR / "credential.json")
initialize_app(credential)


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
        decoded_token = auth.verify_id_token(credential.credentials)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication from Firebase. {err}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    res.headers["WWW-Authenticate"] = 'Bearer realm="auth_required"'
    return decoded_token


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


@app.get("/user_token")
async def hello_user(user=Depends(get_user_token)):
    return {"msg": "Hello, user", "uid": user["uid"]}


class DeployBotRequest(BaseModel):
    bot_name: str
    uid: str
    user: dict = Depends(get_user_token)


@app.post("/deploy")
def deploy(req: DeployBotRequest):
    bot_name = req.bot_name
    uid = req.uid
    s3 = boto3.client("s3")
    with open(BOT_DIR / f"{bot_name}.zip", "wb") as f:
        s3.download_fileobj(AWS_BUCKET_NAME, f"{uid}/{bot_name}.zip", f)

    with open(BOT_DIR / f"{bot_name}.zip", "rb") as f:
        packz = zipfile.ZipFile(f)
        target_dir = BOT_DIR / bot_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in packz.namelist():
            packz.extract(name, target_dir)

    os.remove(BOT_DIR / f"{bot_name}.zip")

    os.system(
        f"""pm2 start bot.py --name "{bot_name}" -- bots/{bot_name}/{bot_name}.json --cog-path=bots.{bot_name}.{bot_name} --dotenv-path=bots/{bot_name}/.env""",
    )
    return {"Hello": "World"}


class StartBotRequest(BaseModel):
    bot_name: str
    user: dict = Depends(get_user_token)


@app.post("/start")
def start_bot(req: StartBotRequest):
    bot_name = req.bot_name
    os.system(
        f"""pm2 start bot.py --name "{bot_name}" -- bots/{bot_name}/{bot_name}.json --cog-path=bots.{bot_name}.{bot_name} --dotenv-path=bots/{bot_name}/.env""",
    )
    return {"Hello": "World"}


class StopBotRequest(BaseModel):
    bot_name: str
    user: dict = Depends(get_user_token)


@app.post("/stop")
def stop_bot(req: StopBotRequest):
    bot_name = req.bot_name
    os.system(f"pm2 stop {bot_name}")
    return {"Hello": "World"}
