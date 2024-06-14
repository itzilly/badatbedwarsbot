import re
from collections.abc import Coroutine
from typing import Callable, Any

import dat
import uuid
import yt_dlp
import discord
import logging
import mcfetch

from discord.utils import get
from discord.ext import commands
from discord import FFmpegPCMAudio
from audio_handler import AudioHandler

from discord.ext.commands import has_permissions


class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.AudioHandler = AudioHandler(bot)

        @bot.command("ping")
        async def ping(ctx: commands.Context):
            """Usage: `.ping`
            Replies with pong!"""
            logging.debug(f"Executing 'ping' Command: {ctx.author.name}")
            await ctx.channel.send('Pong!')

        @bot.command("getlink")
        async def get_link(ctx: commands.Context):
            """Usage: `.getlink`
            Retrieves the link information for the user."""
            message = ctx.message
            link = dat.get_link(str(message.author.id))
            if link is None:
                await message.channel.send("You are not linked")
                return

            await message.channel.send("Link located")

        @bot.command("link")
        async def set_link(ctx: commands.Context):
            """Usage: `.link <discordid> <uuid>`
            Links a Minecraft account to a Discord user.
            `<discordid> is the Discord user ID.`
            `<uuid> is the Minecraft UUID`"""
            message = ctx.message
            info = message.content.split(" ")
            if len(info) != 3:
                await ctx.send(embed=self.get_usage_embed("link", set_link))
                raise ValueError("Invalid arguments")

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
                await message.channel.send(
                    "There was a problem fetching player data. Please check logs for more information")
                print("Exception caught in .link command")
                print("---------------------------------------")
                print(f"Message: {message.content}")
                print(f"Info: {info}")
                print()
                print(e)
                print("---------------------------------------")
                return

        @bot.command("createstarroles")
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
                        await message.channel.send(
                            "There was a problem creating roles. Please check logs for more information")
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

        @bot.command("setrole")
        async def set_role(ctx: commands.Context):
            """Usage: `.setrole <discordid>/<member mention> <roleid>/<prestige>`
            Sets a user's star role.
            `<discordid> is the Discord user ID`
            `<member mention> is @user`
            `<roleid> is the Role's ID'`
            `<prestige> is the star count of the player`"""
            message = ctx.message
            args = message.content.split(" ")
            if len(args) < 3:
                raise ValueError("Invalid argument array")

            mention_pattern = r'^<@\d+>'
            if re.match(mention_pattern, args[1]):
                member_id = args[1][2:].replace(">", "")
            else:
                member_id = args[1]

            member = message.guild.get_member(int(member_id))
            if member is None:
                await message.channel.send(f"Unable to find member from '{args[1]}'")
                raise ValueError("Invalid argument array")

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
                raise ValueError("Invalid argument array")

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

        @bot.command("reload")
        @has_permissions(administrator=True)
        async def reload_commands(ctx: commands.Context):
            """Usage: `.reload`
            Reloads the text command cog"""
            logging.debug(f"Executing 'reload' Command: {ctx.author.name}")
            await bot.unload_extension('text_commands')
            await bot.load_extension('text_commands')

        @bot.command("usage")
        async def usage(ctx: commands.Context):
            await ctx.send(embed=self.get_usage_embed("usage", usage))

        @bot.command("help")
        async def help_command(ctx: commands.Context):
            """Usage: `.showhelp`
            Shows this help message"""
            commands_embed = discord.Embed(
                colour=discord.Colour.blurple(),
                title="Commands",
                description="Text command prefix: `.`"
            )

            for command in bot.commands:
                docstring = command.callback.__doc__
                commands_embed.add_field(
                    name=command.name,
                    value=docstring or "No description available.",
                    inline=False
                )

            await ctx.send(embed=commands_embed)


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog {self.__class__.__name__} is ready.")

    def get_usage_embed(self, command_name: str, func: Callable[..., Coroutine[Any, Any, None]]):
        usage = "NOT_IMPL"
        if not func.__doc__.startswith("A class that implements the protocol for a bot text command"):
            usage = func.__doc__
        return discord.Embed(colour=discord.Colour.red(),
                             title=f"Command Usage for '{command_name}':",
                             description=usage)


async def setup(bot):
    logging.debug("Adding cog: TextCommands")
    await bot.add_cog(TextCommands(bot))
