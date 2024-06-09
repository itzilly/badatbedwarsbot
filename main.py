import os
import discord
import importlib
import txtcmds


commands = txtcmds.commands
usages = txtcmds.usages


def reload_commands():
    global commands, usages
    importlib.reload(txtcmds)
    commands = txtcmds.commands
    usages = txtcmds.usages


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
                usage_embed = discord.Embed(colour=discord.Colour.red(),
                                            title=f"Command Usage for '{command}':",
                                            description=usages.get(command, 'NO-USAGE-IMPL'))
                await message.channel.send(embed=usage_embed)
                print(f"----------------------------")
                print(f"Error executing command: {command}")
                print(f"Details: '{e}'")
                print(f"----------------------------")
        else:
            await message.channel.send("Command not found.")
            commands_embed = discord.Embed(colour=discord.Colour.blurple(),
                                           title="Commands",
                                           description="Text command prefix: `.`")
            for command in commands:
                commands_embed.add_field(name=command, value=usages.get(command, 'NO-USAGE-IMPL'), inline=False)
            await message.channel.send(embed=commands_embed)


    client.run(token)
