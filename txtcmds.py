import os
import dat
import discord
import mcfetch
import requests

from collections import OrderedDict

commands = {}
usages = {}


def sort_commands_dict():
    global commands, usages
    commands = OrderedDict(sorted(commands.items()))
    usages = OrderedDict(sorted(usages.items()))


def txtcmd(command_name):
    def decorator(func):
        commands[command_name] = func
        usages[command_name] = func.__doc__
        sort_commands_dict()
        return func

    return decorator


@txtcmd("ping")
async def ping(message: discord.Message):
    """Usage: `.ping`
    Responds with 'pong'."""
    await message.channel.send("pong")


@txtcmd("testkey")
async def test_key(message: discord.Message):
    """Usage: `.testkey`
    Tests the API key and returns status and rate limit."""
    key = os.environ['API_KEY']
    url = "https://api.hypixel.net/v2/player?uuid=5328930e-d411-49cb-90ad-4e5c7b27dd86"
    req = requests.get(url, params={'API-Key': key})
    response = f"Status Code {req.status_code}\n" \
               f"Success: {req.json().get('success', False)}\n" \
               f"Limit Remaining: {req.headers.get('ratelimit-remaining', -1)}"
    await message.channel.send(response)


@txtcmd("link")
async def link_user(message: discord.Message):
    """Usage: `.link <discordid> <uuid>`
    Links a Minecraft account to a Discord user."""
    info = message.content.split(" ")
    if len(info) != 3:
        await message.channel.send(usages["link_user"])
        return

    member = message.guild.get_member(int(info[1]))
    if not member:
        await message.channel.send("Unknown member")
        return

    try:
        if not mcfetch.is_valid_uuid(info[2]):
            await message.channel.send(f"Invalid UUID: `{info[2]}`")
            return

        player = mcfetch.AsyncPlayer(player=info[2])
        player_name = await player.name
        player_uuid = await player.uuid
        if player_uuid is None:
            await message.channel.send(f"Unable to fetch player name/uuid `{info[2]}`")
            return
    except Exception as e:
        await message.channel.send("There was a problem fetching player data. Please check logs for more information")
        print("Exception caught in .link command")
        print("---------------------------------------")
        print(f"Message: {message.content}")
        print(f"Info: {info}")
        print()
        print(e)
        print("---------------------------------------")
        return

    nickname = member.nick
    if nickname is None:
        nickname = member.name
    try:
        successful = dat.set_link(discid=info[1], uuid=player_uuid, ign=player_name, nickname=nickname)
    except Exception as e:
        await message.channel.send("There was a problem executing the command. Please check logs for more information")
        print("Exception caught in .link command")
        print("---------------------------------------")
        print(f"Message: {message.content}")
        print(f"Info: {info}")
        print()
        print(e)
        print("---------------------------------------")
        return

    if successful:
        await message.channel.send(f"Linked {member.mention} to `{player_name}` (nick: `{nickname}`)")
        return

    await message.channel.send("Link failed. Check logs for more information")
    print(f"Message: {message.content}")
    print(f"Info: {info}")


@txtcmd("getlink")
async def get_link(message: discord.Message):
    """Usage: `.getlink`
    Retrieves the link information for the user."""
    link = dat.get_link(str(message.author.id))
    if link is None:
        await message.channel.send("You are not linked")
        return

    await message.channel.send("Link located")


@txtcmd("rolestar")
async def set_user_star_role_auto(message: discord.Message):
    """Usage: `.rolestar <discordid>/<member mention>
    Sets a user's star role."""
    