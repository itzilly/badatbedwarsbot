import errors
import yt_dlp
import logging
import discord
import functools

from typing import List
from discord.ext import commands
from dataclasses import dataclass
from discord import VoiceClient, FFmpegPCMAudio


@dataclass
class ServerDetails:
    queue: List
    guild_id: int
    voice_client: VoiceClient


class AudioHandler:
    def __init__(self, bot):
        self._bot = bot
        self._server_details: List[ServerDetails] = []

    def _exists_player(self, guild_id: int) -> bool:
        for server in self._server_details:
            if guild_id == server.guild_id:
                return True
        return False

    def get_server_details(self, guild_id: int) -> ServerDetails | None:
        for server in self._server_details:
            if server.guild_id == guild_id:
                return server
        return None

    def register_player_by_context(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        if self._exists_player(guild_id):
            raise errors.PlayerAlreadyRegisteredError(guild_id)

        server_details = ServerDetails(
            queue=[],
            guild_id=ctx.guild.id,
            voice_client=discord.utils.get(self._bot.voice_clients, guild=ctx.guild)
        )
        self._server_details.append(server_details)

    def register_player(self, sd: ServerDetails):
        guild_id = sd.guild_id
        if self._exists_player(guild_id):
            raise errors.PlayerAlreadyRegisteredError(guild_id)

        self._server_details.append(sd)

    def add_to_queue_by_context(self, ctx: commands.Context, search: str) -> bool:
        for server in self._server_details:
            if ctx.guild.id == server.guild_id:
                server.queue.append(search)
                return True
        return False

    def add_to_queue_guild_id(self, guild_id: int, search: str) -> bool:
        for server in self._server_details:
            if guild_id == server.guild_id:
                server.queue.append(search)
                return True
        return False

    async def play_by_context(self, ctx: commands.Context) -> bool:
        server_details: ServerDetails = None
        for server in self._server_details:
            if ctx.guild.id == server.guild_id:
                server_details = server

        if server_details is None:
            return False

        connected = server_details.voice_client.is_connected()

        if not server_details.voice_client.is_connected():
            voice_channel = ctx.author.voice.channel
            server_details.voice_client = await voice_channel.connect(reconnect=True)

        ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        _, _, url = self.search(server_details.queue[0])

        after_playing = functools.partial(self._after_playing, guild_id=server_details.guild_id)
        server_details.voice_client.play(FFmpegPCMAudio(url, **ffmpeg_opts), after=after_playing)

    async def play_by_guild_id(self, guild_id: int) -> bool:
        voice_client = None
        server_details: ServerDetails = None
        for server in self._server_details:
            if guild_id == server.guild_id:
                server_details = server

        if server_details is None:
            return False

        voice_client = server_details.voice_client

        if voice_client is None:
            return False

        ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        _, _, url = self.search(server_details.queue[0])

        after_playing = functools.partial(self._after_playing, guild_id=server_details.guild_id)
        server_details.voice_client.play(FFmpegPCMAudio(url, **ffmpeg_opts), after=after_playing)

    def pause_by_context(self, ctx: commands.Context) -> bool:
        voice_client = discord.utils.get(self._bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            return True
        return False

    def pause_by_guild_id(self, guild_id: int) -> bool:
        voice_client = discord.utils.get(self._bot.voice_clients, guild=self._bot.get_guild(guild_id))
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            return True
        return False

    def resume_by_context(self, ctx: commands.Context) -> bool:
        voice_client: VoiceClient = discord.utils.get(self._bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            return True
        return False

    def resume_by_guild_id(self, guild_id) -> bool:
        voice_client: VoiceClient = discord.utils.get(self._bot.voice_clients, guild=self._bot.get_guild(guild_id))
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            return True
        return False

    def _after_playing(self, e: Exception, guild_id: int):
        if e:
            logging.fatal(e)

        server_details: ServerDetails = None
        for server in self._server_details:
            if server.guild_id == guild_id:
                server_details = server
        if server_details is None:
            return

        server_details.queue.pop(0)
        if len(server_details.queue) == 0:
            return
        self.play_by_guild_id(server_details.guild_id)

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
