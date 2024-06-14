import os
import asyncio
import logging
from typing import Optional

import discord
import traceback

from discord.ext import commands
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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    prefix = '.'
    description = "Bad at Bedwars Discord Bot"

    bot = BadAtBedwarsBot(command_prefix=prefix, description=description, intents=discord.Intents.all())
    token = os.environ['TOKEN']
    if token is None:
        logging.error("No token found! Aborting start")
        exit(401)

    asyncio.run(bot.start(token))
