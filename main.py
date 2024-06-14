import os
import sys
import gzip
import shutil
import asyncio
import discord
import logging
import argparse
import traceback

from typing import Optional
from discord.ext import commands
from colorama import init, Fore, Style
from logging.handlers import RotatingFileHandler
from discord.ext.commands import HelpCommand, MinimalHelpCommand


class BadAtBedwarsBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logging.info(f"Logged in as {self.user}")

    async def setup_hook(self):
        try:
            await self.load_extension('text_commands')
        except Exception as e:
            logging.error(f"Failed to load extension 'text_commands' extension: {e}")
            traceback.print_exc()

    async def help_command(self) -> Optional[HelpCommand]:
        return MinimalHelpCommand()

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found!")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You must be administrator to run this command!")

        else:
            await ctx.send("An error has occurred!")
            print(error)
            traceback.print_exc()

    # async def help_command(self) -> Optional[HelpCommand]:
    #     help_command = HelpCommand()
    #     help_command.


class CustomFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.FORMATS = {
            logging.DEBUG: self.format_message(Fore.CYAN),
            logging.INFO: self.format_message(Fore.GREEN),
            logging.WARNING: self.format_message(Fore.YELLOW),
            logging.ERROR: self.format_message(Fore.RED),
            logging.CRITICAL: self.format_message(Fore.RED + Style.BRIGHT)
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

    def format_message(self, level_color):
        time_color = Fore.LIGHTBLACK_EX
        level_bold = Style.BRIGHT
        root_color = Fore.MAGENTA
        message_color = Fore.WHITE

        return f"{time_color}%(asctime)s{Style.RESET_ALL} " \
               f"{level_color}{level_bold}%(levelname)-8s{Style.RESET_ALL} " \
               f"{root_color}%(name)-15s{Style.RESET_ALL} " \
               f"{message_color}%(message)s{Style.RESET_ALL}"


def setup_logger(stdout_level=logging.INFO):
    init()
    discord_log_filename = os.path.join("logs", "discord.log")
    max_log_size = 1024 * 1024 * 100  # 10 MB

    # Ensure the logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Compress and archive the old log file (if it exists) when the bot starts up
    try:
        if os.path.exists(discord_log_filename):
            log_time_timestamp = int(os.path.getctime(discord_log_filename))
            archive_filename = f"{discord_log_filename}.{log_time_timestamp}.gz"

            with open(discord_log_filename, 'rb') as f_in:
                with gzip.open(archive_filename, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            os.remove(discord_log_filename)
    except Exception as e:
        print(f"Error archiving log file: {e}")

    # Define the log format
    datetime_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter('[%(name)s] [%(asctime)s %(levelname)s] %(message)s', datetime_format)

    discord_log_handler = RotatingFileHandler(discord_log_filename, maxBytes=max_log_size, backupCount=0,
                                              encoding="utf8")
    discord_log_handler.setLevel(logging.DEBUG)
    discord_log_handler.setFormatter(formatter)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(stdout_level)
    stdout_handler.setFormatter(CustomFormatter())

    # Configure the root logger
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt=datetime_format,
        format='[%(name)s] [%(asctime)s %(levelname)s] %(message)s',
        handlers=[
            discord_log_handler,
            stdout_handler
        ]
    )

    # Set the specific log levels for other loggers
    logging.getLogger('discord').setLevel(logging.DEBUG)
    logging.getLogger('root').setLevel(logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.INFO)

    logging.debug("Logger setup complete")


if __name__ == '__main__':
    # Parse command line arguments (verbose logger)
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Show debug level logs")
    cli_args = parser.parse_args()

    if cli_args.verbose:
        setup_logger(logging.DEBUG)
    else:
        setup_logger()

    prefix = '.'
    description = "Bad at Bedwars Discord Bot"

    bot = BadAtBedwarsBot(command_prefix=prefix, description=description, intents=discord.Intents.all())
    token = os.environ.get('TOKEN')
    if not token:
        logging.error("No token found! Aborting start")
        sys.exit(401)

    asyncio.run(bot.start(token))
