import os
import discord
import importlib
import txtcmds
from txtcmds import commands, txtcmd


def reload_commands():
    global commands
    importlib.reload(txtcmds)
    commands = txtcmds.commands


if __name__ == '__main__':
    token = os.environ['TOKEN']
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)


    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")


    @client.event
    async def on_message(message: discord.Message):
        if not message.content.startswith("."):
            return

        if not message.author.guild_permissions.administrator:
            return

        content = message.content[1:]
        command, *args = content.split()
        if command == "reload":
            try:
                reload_commands()
                await message.channel.send("Commands reloaded successfully.")
            except Exception as e:
                await message.channel.send("Failed to reload commands. Check logs for more information.")
                print(e)
        elif command in commands:
            try:
                await commands[command](message)
            except Exception as e:
                await message.channel.send("There was a problem with your request. Check logs for more information.")
                print(e)
        else:
            await message.channel.send("Command not found.")


    client.run(token)
