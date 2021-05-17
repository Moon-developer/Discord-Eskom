import sqlite3
from os import getenv

from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv

from cogs.eskom_cog import EskomCog
from core.eskom_interface import EskomInterface

load_dotenv()


class Deskom:

    def __init__(self):
        # setup bot
        self.token = getenv('DISCORD_TOKEN')
        self.cogs = [
            {'name': 'Eskom', 'obj': EskomCog, 'active': True},
        ]
        self.bot = commands.Bot(command_prefix='!eskom ', case_insensitive=False)

        # database connection
        self.con = sqlite3.connect('eskom.sqlite.db')
        self.setup_tables()

        # access to eskom interface
        self.eskom_interface = EskomInterface()

        # assign connection to bot
        setattr(self.bot, 'con', self.con)
        setattr(self.bot, 'eskom_interface', self.eskom_interface)

        # init functions
        self.init_cogs()
        self.add_events()

    def setup_tables(self):
        cursor = self.con.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS '
            'channels('
            '   id integer PRIMARY KEY,'
            '   guild_name TEXT NOT NULL,'
            '   guild_id TEXT NOT NULL UNIQUE,'
            '   channel_name TEXT NOT NULL,'
            '   channel_id TEXT NOT NULL UNIQUE,'
            '   announce INTEGER DEFAULT 1 NOT NULL'
            ')'
        )
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS '
            'eskom_stage('
            '   id integer PRIMARY KEY,'
            '   stage INTEGER NOT NULL'
            ')'
        )

    async def announce_stage_change(self, cursor, stage):
        cursor.execute('SELECT channel_id FROM channels WHERE announce = "1"')
        rows = cursor.fetchall()
        for row in rows:
            channel = self.bot.get_channel(int(row[0]))
            await channel.send(f'Update! stage has changed to {stage}')
        self.con.commit()

    @tasks.loop(seconds=60)
    async def lookup_eskom_stage(self):
        await self.bot.wait_until_ready()
        cursor = self.con.cursor()
        stage = await self.eskom_interface.async_get_stage()
        cursor.execute('SELECT stage FROM eskom_stage ORDER BY ROWID DESC LIMIT 1')
        old_stage = cursor.fetchone()
        old_stage = old_stage[0] if old_stage else old_stage
        if stage != old_stage:
            cursor.execute('INSERT INTO eskom_stage(stage) VALUES (?)', (stage,))
            self.con.commit()
            await self.announce_stage_change(cursor=cursor, stage=stage)
        cursor.close()

    def init_cogs(self):
        for cog in self.cogs:
            self.bot.add_cog(cog['obj'](self.bot))

    async def on_ready(self):
        print(f'{self.bot.user.name} is connected.')

    def add_events(self):
        self.bot.event(self.on_ready)

    def start_bot(self):
        self.lookup_eskom_stage.start()
        self.bot.run(self.token)


if __name__ == '__main__':
    client = Deskom()
    client.start_bot()
