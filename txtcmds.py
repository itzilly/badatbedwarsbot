import os
import re

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


def get_usage_embed(command_name):
    return discord.Embed(colour=discord.Colour.red(),
                         title=f"Command Usage for '{command_name}':",
                         description=usages.get(command_name, 'NO-USAGE-IMPL'))


@txtcmd("ping")
async def ping(message: discord.Message):
    """Usage: `.ping`
    Responds with 'pong'."""
    await message.channel.send("pong")


@txtcmd("bedwars")
async def bedwars(message: discord.Message):
    """Usage: `.bedwars`
    Responds with ur mother."""
    await message.channel.send("bedwars stats")


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
    Links a Minecraft account to a Discord user.
    `<discordid> is the Discord user ID.`
    `<uuid> is the Minecraft UUID`"""
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


@txtcmd("createstarroles")
async def create_starroles(message: discord.Message):
    """Usage: `createstarroles`
    Creates all star roles.
    NOTE: **DANGEROUS COMMAND**"""
    await message.channel.send("This command has been disabled")
    return

    roles_to_be_created = []
    roles = []
    for star_role in dat.StarPrestiges[::-1]:  # Go backwards so higher star roles have higher priority
        # FIXME: This OR thing will always run no matter what, since the star role id's aren't set (wrong operation)
        if star_role.roleid is None or star_role.roleid not in message.guild.roles:
            roles_to_be_created.append(star_role.prestige)
            role_color = discord.Colour.from_str(star_role.color)
            try:
                role = await message.guild.create_role(
                    name=star_role.prestige,
                    colour=role_color)

                await message.channel.send(embed=discord.Embed(
                    color=role_color,
                    description=f"Created {role.mention}"))

                roles.append(role)
                dat.update_star_role_id(star_role, role.id)
            except Exception as e:
                await message.channel.send("There was a problem creating roles. Please check logs for more information")
                print("Exception caught in .createstarroles command")
                print("---------------------------------------")
                print(f"Message: {message.content}")
                print(f"Star Role: {star_role}")
                print(f"  name: {star_role.prestige}")
                print(f"  colour hex: {star_role.color}")
                print()
                print(e)
                print("---------------------------------------")

    await message.channel.send(f"Done")


@txtcmd("setrole")
async def set_user_star_role_auto(message: discord.Message):
    """Usage: `.setrole <discordid>/<member mention> <roleid>/<prestige>`
    Sets a user's star role.
    `<discordid> is the Discord user ID`
    `<member mention> is @user`
    `<roleid> is the Role's ID'`
    `<prestige> is the star count of the player`"""
    args = message.content.split(" ")
    if len(args) < 3:
        await message.channel.send(embed=get_usage_embed("setrole"))
        return

    mention_pattern = r'^<@\d+>'
    if re.match(mention_pattern, args[1]):
        member_id = args[1][2:].replace(">", "")
    else:
        member_id = args[1]

    member = message.guild.get_member(int(member_id))
    if member is None:
        await message.channel.send(f"Unable to find member from '{args[1]}'")
        await message.channel.send(embed=get_usage_embed("rolestar"))
        return

    role = None
    try:
        role = message.guild.get_role(int(args[2]))
    except Exception as e:
        await message.channel.send(f"There was a problem fetching role. Please check logs for more information")
        print("Exception caught in .setrole command")
        print("---------------------------------------")
        print(f"Message: {message.content}")
        print(f"Args: {args}")
        print()
        print(e)
        print("---------------------------------------")
        await message.channel.send(embed=get_usage_embed("setrole"))
        return

    if role is not None:
        try:
            await member.add_roles(role)
            await message.channel.send(
                embed=discord.Embed(
                    color=role.color,
                    description=f"Added {role.mention} to {member.mention}"))
            return
        except Exception as e:
            print("Exception caught in .setrole command")
            print("---------------------------------------")
            print(f"Message: {message.content}")
            print(f"Args: {args}")
            print(f"Member: {member.__str__()}")
            print()
            print(e)
            print("---------------------------------------")
            return

    try:
        stars = int(args[2])
    except ValueError as e:
        await message.channel.send(embed=discord.Embed(description=f"Invalid int: `{args[2]}`"))
        return

    if stars < 100:
        prestige_role = dat.StonePrestige
    elif 100 <= stars < 200:
        prestige_role = dat.IronPrestige
    elif 200 <= stars < 300:
        prestige_role = dat.GoldPrestige
    elif 300 <= stars < 400:
        prestige_role = dat.DiamondPrestige
    elif 400 <= stars < 500:
        prestige_role = dat.EmeraldPrestige
    elif 500 <= stars < 600:
        prestige_role = dat.SapphirePrestige
    elif 600 <= stars < 700:
        prestige_role = dat.RubyPrestige
    elif 700 <= stars < 800:
        prestige_role = dat.CrystalPrestige
    elif 800 <= stars < 900:
        prestige_role = dat.OpalPrestige
    elif 900 <= stars < 1000:
        prestige_role = dat.AmethystPrestige
    else:
        await message.channel.send("Star count too high!")
        return

    role_id = dat.fetch_role_id(prestige_role)
    role = message.guild.get_role(role_id)
    if role is None:
        await message.channel.send(f"Unable to find role from '{args[1]}'")
        return

    try:
        await member.add_roles(role)
        await message.channel.send(embed=discord.Embed(
            color=role.color,
            description=f"Added {role.mention} to {member.mention}"))
        return
    except Exception as e:
        print("Exception caught in .setrole command")
        print("---------------------------------------")
        print(f"Message: {message.content}")
        print(f"Args: {args}")
        print(f"Member: {member.__str__()}")
        print(f"Role ID: {role_id}")
        print()
        print(e)
        print("---------------------------------------")
    await message.channel.send(f"An error has occurred, please check logs for more information")
