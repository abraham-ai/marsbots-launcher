import argparse
import atexit
import json
import logging
import os
from pathlib import Path

import discord
from discord import SyncWebhook
from discord.ext import commands
from dotenv import load_dotenv
from marsbots import constants
from marsbots.models import MarsBotMetadata


class MarsBot(commands.Bot):
    def __init__(self, metadata_path: str) -> None:
        intents = discord.Intents.default()
        self.metadata = self.load_metadata(metadata_path)
        self.set_intents(intents)
        self.configure_logging()
        commands.Bot.__init__(
            self,
            command_prefix=self.metadata.command_prefix,
            intents=intents,
        )
        atexit.register(self.post_exit_webhook)

    def load_metadata(self, metadata_path: str) -> MarsBotMetadata:
        metadata = json.load(open(metadata_path))
        if "command_prefix" not in metadata:
            # Hack to allow a bot without command prefix
            metadata["command_prefix"] = constants.UNLIKELY_PREFIX
        if "intents" not in metadata:
            metadata["intents"] = []
        return MarsBotMetadata(**metadata)

    def set_intents(self, intents: discord.Intents) -> None:
        intents.message_content = True
        intents.messages = True
        if "presence" in self.metadata.intents:
            intents.presences = True
        if "members" in self.metadata.intents:
            intents.members = True

    def configure_logging(self) -> None:
        logdir = constants.LOG_DIR / self.metadata.name
        logfile = str(logdir / "discord.log")
        logdir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%a, %d %b %Y %H:%M:%S",
            filename=logfile,
            filemode="w",
            force=True,
        )

    async def on_ready(self) -> None:
        print(f"Running {self.metadata.name}...")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    def post_exit_webhook(self):
        webhook_url = os.getenv("CRASH_WEBHOOK_URL")
        if webhook_url:
            try:
                webhook = SyncWebhook.from_url(webhook_url)
                webhook.send(f"{self.metadata.name} is down.")
            except Exception as e:
                logging.error("Unable to post exit to webhook.")
                logging.error(str(e))


def start(
    bot_name: str,
    metadata_path: str,
    cog_paths: str,
    dotenv_path: str = constants.DOTENV_PATH,
) -> None:

    bot_dir = Path(__file__).parent / "bots" / bot_name
    metadata_path = metadata_path or bot_dir / "metadata.json"
    cog_paths = cog_paths or [f"bots.{bot_name}.{bot_name}"]
    dotenv_path = dotenv_path or bot_dir / ".env"

    print("Launching bot...")
    load_dotenv(dotenv_path)

    bot = MarsBot(metadata_path)
    for path in cog_paths:
        res = bot.load_extension(path)
        if type(res[path]) != bool:
            raise Exception(res[path])
    bot.run(os.getenv(bot.metadata.token_env))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarsBot")
    parser.add_argument("bot_name", help="Name of the bot to load from /bots directory")
    parser.add_argument("--metadata_path", help="Path to a custom metadata file")
    parser.add_argument(
        "--cog-paths",
        help="Path to one or more cog files to load, using python module syntax",
        nargs="+",
        default=[],
    )
    parser.add_argument("--dotenv-path", help="Path to a custom .env file")
    args = parser.parse_args()
    start(args.bot_name, args.metadata_path, args.cog_paths, args.dotenv_path)
