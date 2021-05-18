# -*- coding: utf-8 -*-
""" Eskom Cog.
This module contains the Eskom cog that provides the bot with argument functionality in Discord.

Discord chat usage:
    > !eskom help
    > !eskom announce #channel-name
    > !eskom disable
    > !eskom stage
"""
from sqlite3 import Cursor

from discord.ext import commands
from discord.ext.commands.context import Context


class EskomCog(commands.Cog):
    """ Discord bot Eskom Cog argument parser """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='stage', brief="get latest eskom stage")
    async def stage(self, ctx: Context):
        """
        Get the latest stage from the database
        :param ctx: channel context
        """
        cursor: Cursor = self.bot.con.cursor()
        cursor.execute('SELECT stage FROM eskom_stage ORDER BY ROWID DESC LIMIT 1')
        row = cursor.fetchone()
        stage = row[0] if row else 0
        await ctx.channel.send(f'Currently on stage {stage} !')

    @staticmethod
    def already_announcing(cursor: Cursor, guild_id: str) -> bool:
        """
        Check if already announcing in current guild
        :param cursor: sqlite db cursor
        :param guild_id: current guild id to check
        :return: True if already announcing else False
        """
        cursor.execute('SELECT guild_id FROM channels WHERE guild_id = (?)', (guild_id,))
        row = cursor.fetchone()
        return bool(row)

    def update_announcement_channel(self, cursor: Cursor, guild, channel):
        """
        Updates the announcement channel for current guild to the new channel
        :param cursor: sqlite db cursor
        :param guild: current guild to update
        :param channel: new channel to announce in
        """
        cursor.execute(
            'UPDATE channels SET channel_id = ?, channel_name = ?, announce = ? WHERE guild_id = ?',
            (channel.id, channel.name, 1, guild.id)
        )
        self.bot.con.commit()

    def create_new_announcement(self, cursor: Cursor, guild, channel):
        """
        Creates a new entry in the database to announce load-shedding schedules.
        :param cursor: sqlite db cursor
        :param guild: current guild to create
        :param channel: channel to announce in
        """
        cursor.execute(
            'INSERT OR IGNORE INTO channels (guild_id, guild_name, channel_id, channel_name) VALUES (?,?,?,?)',
            (guild.id, guild.name, channel.id, channel.name)
        )
        self.bot.con.commit()

    async def confirm_command(self, ctx: Context):
        """
        Asks user to confirm command parsed.
        :param ctx: channel Context
        """
        await ctx.channel.send('Are you sure you want to announce here?. `y/N`')

        def check(message):
            return message.channel == ctx.channel and message.content.lower() in ['y', 'yes']

        await self.bot.wait_for("message", check=check, timeout=30)

    @commands.is_owner()
    @commands.command(name='disable', brief="Stop announcing load-shedding.")
    async def disable(self, ctx: Context):
        """
        Updates the current guilds `announce` column to 0 to disable announcements.
        :param ctx: channel Context
        """
        await self.confirm_command(ctx=ctx)
        cursor: Cursor = self.bot.con.cursor()
        cursor.execute('SELECT guild_id FROM channels WHERE guild_id = (?)', (ctx.guild.id,))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                'UPDATE channels SET announce = ? WHERE guild_id = ?',
                (0, ctx.guild.id)
            )
            self.bot.con.commit()
            cursor.close()
            await ctx.channel.send('No longer announcing load-shedding stages.')
        else:
            await ctx.channel.send('There isn\'t a channel currently assigned to disable.')

    @commands.is_owner()
    @commands.command(name='announce', brief="Set channel to announce to.")
    async def announce(self, ctx: Context, announce_channel: str):
        """
        Create/Update guild announcement channel for bot to announce load-shedding stages.
        :param ctx: channel Context
        :param announce_channel: channel to announce in
        """
        new_channel = None
        for channel in ctx.guild.text_channels:
            if str(channel.id) == announce_channel[2:-1]:
                new_channel = channel
        if new_channel:
            await self.confirm_command(ctx=ctx)
            cursor: Cursor = self.bot.con.cursor()
            if self.already_announcing(cursor=cursor, guild_id=ctx.guild.id):
                self.update_announcement_channel(cursor=cursor, guild=ctx.guild, channel=new_channel)
            else:
                self.create_new_announcement(cursor=cursor, guild=ctx.guild, channel=new_channel)
            cursor.close()
            await ctx.channel.send(f'Now announcing load-shedding stages in {new_channel.name}')
        else:
            await ctx.channel.send('That is not a valid/existing text channel.')

    @announce.error
    async def announce_error(self, ctx, error):
        """
        Handles announce command Missing channel name error.
        :param ctx: channel Context
        :param error: error thrown
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify a channel with # followed by channel name.')
