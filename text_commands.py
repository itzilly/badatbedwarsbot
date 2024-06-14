import re

import dat
import uuid
import yt_dlp
import discord
import logging
import mcfetch

from discord.ext import commands
from typing import Callable, Any
from audio_handler import AudioHandler
from collections.abc import Coroutine
from errors import PlayerAlreadyRegisteredError
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

        @bot.command("join")
        async def connect_voice(ctx: commands.Context):
            logging.debug(f"Executing 'join' Command: {ctx.author.name}")
            if ctx.author.voice is None:
                await ctx.send("You are not connected to a voice channel!")
                return

            try:
                await ctx.author.voice.channel.connect(self_deaf=True)
            except discord.errors.ClientException as e:
                if str(e) == "Already connected to a voice channel.":
                    await ctx.send("I'm already connected to a voice channel!")
            except Exception as e:
                error_id = uuid.uuid4()
                await ctx.send(f"An error has occurred! Please check logs for more information: {error_id}")

        @bot.command("dc")
        async def disconnect_voice(ctx: commands.Context):
            # TODO: Make this command disconnect the bot if it's in ANY voice channel
            # Right now it only dc's if the user who sends the command is in the same  channel
            logging.debug(f"Executing 'dc' Command: {ctx.author.name}")
            for x in bot.voice_clients:
                if x.channel == ctx.author.voice.channel:
                    return await x.disconnect(force=True)

        @bot.command("play")
        async def play_command(ctx: commands.Context):
            logging.debug(f"Executing 'play' Command: {ctx.author.name}")
            audio_channel = ctx.author.voice.channel
            if audio_channel is None:
                await ctx.send("You are not connected to a voice channel!")
                return

            try:
                stream_connection = await audio_channel.connect(reconnect=True)
                self.AudioHandler.get_server_details(ctx.guild.id).voice_channel = stream_connection
            except Exception as e:
                pass

            try:
                self.AudioHandler.register_player_by_context(ctx)
            except PlayerAlreadyRegisteredError as e:
                await ctx.send(f"Failed to register player: {e}")

            search_terms = ctx.message.content.replace(".play", "").strip()
            if not search_terms:
                await ctx.send(f"Now playing...")
                await self.AudioHandler.play_by_context(ctx)
                return

            self.AudioHandler.add_to_queue_by_context(ctx, search_terms)
            await self.AudioHandler.play_by_context(ctx)

        @bot.command("pause")
        async def pause_command(ctx: commands.Context):
            logging.debug(f"Executing 'pause' Command: {ctx.author.name}")
            self.AudioHandler.pause_by_context(ctx)

        @bot.command("resume")
        async def resume_command(ctx: commands.Context):
            logging.debug(f"Executing 'resume' Command: {ctx.author.name}")
            self.AudioHandler.resume_by_context(ctx)

        @bot.command("add")
        async def add_song_to_queue(ctx: commands.Context):
            logging.debug(f"Executing 'add' Command: {ctx.author.name}")
            search_terms = ctx.message.content.replace(".add", "").strip()
            if not search_terms:
                await ctx.send("Oh no! You didn't specify a song! Please try again.")
                return

            success = self.AudioHandler.add_to_queue_by_context(ctx, search_terms)
            if success:
                await ctx.send(f"Added {search_terms} to queue.")
                return
            else:
                await ctx.send(f"Failed to add {search_terms} to queue.")

        @bot.command("registerplayer")
        async def register_player(ctx: commands.Context):
            try:
                self.AudioHandler.register_player_by_context(ctx)
                await ctx.send(f"Registered player: {ctx.guild.id}")
            except PlayerAlreadyRegisteredError as e:
                await ctx.send(f"Failed to register player: {e}")

        @bot.command("rp")
        async def register_player_alias(ctx: commands.Context):
            await register_player(ctx)

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

    def search(self, query):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in search_results and len(search_results['entries']) > 0:
                video = search_results['entries'][0]
                audio_info = ydl.extract_info(video['url'], download=False)
                audio_url = audio_info['url']
                return video['url'], video['title'], audio_url
            else:
                return None, None, None

    def after_playing(self, e: Exception):
        if e:
            logging.error(e)

        self.AudioHandler._is_playing = False
        self.AudioHandler.current_has_finished = True
        self.AudioHandler.play_next()


async def setup(bot):
    logging.debug("Adding cog: TextCommands")
    await bot.add_cog(TextCommands(bot))
