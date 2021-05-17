from sqlite3 import Cursor

from discord.ext import commands
from discord.ext.commands.context import Context


class EskomCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='stage', brief="get latest eskom stage")
    async def stage(self, ctx: Context):
        cursor: Cursor = self.bot.con.cursor()
        cursor.execute('SELECT stage FROM eskom_stage ORDER BY ROWID DESC LIMIT 1')
        row = cursor.fetchone()
        stage = row[0] if row else 0
        await ctx.channel.send(f'Currently on stage {stage} !')

    @staticmethod
    def already_announcing(cursor: Cursor, guild_id: str) -> bool:
        cursor.execute('SELECT guild_id FROM channels WHERE guild_id = (?)', (guild_id,))
        row = cursor.fetchone()
        return True if row else False

    def update_announcement_channel(self, cursor: Cursor, guild, channel):
        cursor.execute(
            'UPDATE channels SET channel_id = ?, channel_name = ?, announce = ? WHERE guild_id = ?',
            (channel.id, channel.name, 1, guild.id)
        )
        self.bot.con.commit()

    def create_new_announcement(self, cursor: Cursor, guild, channel):
        cursor.execute(
            'INSERT OR IGNORE INTO channels (guild_id, guild_name, channel_id, channel_name) VALUES (?,?,?,?)',
            (guild.id, guild.name, channel.id, channel.name)
        )
        self.bot.con.commit()

    async def confirm_command(self, ctx: Context):
        await ctx.channel.send('Are you sure you want to announce here?. `y/N`')

        def check(m):
            return m.channel == ctx.channel and m.content.lower() in ['y', 'yes']

        await self.bot.wait_for("message", check=check, timeout=30)

    @commands.is_owner()
    @commands.command(name='disable', brief="Stop announcing load-shedding.")
    async def disable(self, ctx: Context):
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
            await ctx.channel.send(f'No longer announcing load-shedding stages.')
        else:
            await ctx.channel.send('There isn\'t a channel currently assigned to disable.')

    @commands.is_owner()
    @commands.command(name='announce', brief="Set channel to announce to.")
    async def announce(self, ctx: Context, announce_channel: str):
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
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Please specify a channel with # followed by channel name.')
