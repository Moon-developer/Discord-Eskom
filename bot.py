# -*- coding: utf-8 -*-
""" Discord Bot Main.
This module contains the Deskom bot class that takes an optional token argument.

Usage:
    $ python3 bot.py --token <your-token-here>
"""
import argparse
import sqlite3
from os import getenv
from sqlite3 import Cursor

from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv

from cogs.eskom_cog import EskomCog
from core.eskom_interface import EskomInterface

load_dotenv()


class Deskom:
    """ Eskom Bot Class """

    def __init__(self, token: str = None):
        # setup bot
        self.token = token if token else getenv('DISCORD_TOKEN')
        if not self.token:
            raise Exception('Token missing. Make sure token is set in your env or passed as an argument.')

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
        """ Create `channels` and `eskom_stage` tables if not already created """
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

    async def announce_stage_change(self, cursor: Cursor, stage: str):
        """
        Query all channels to announce. Loop through channels and announce new stage one at a time.
        :param cursor: database cursor
        :param stage: current load-shedding stage to announce
        :return:
        """
        cursor.execute('SELECT channel_id FROM channels WHERE announce = "1"')
        rows = cursor.fetchall()
        for row in rows:
            channel = self.bot.get_channel(int(row[0]))
            await channel.send(f'Update! stage has changed to {stage}')
        self.con.commit()

    @tasks.loop(seconds=60)
    async def lookup_eskom_stage(self):
        """ Long running looping task that queries Eskom page for latest stage and announces if changed """
        await self.bot.wait_until_ready()
        cursor = self.con.cursor()
        stage = await self.eskom_interface.async_get_stage()
        cursor.execute('SELECT stage FROM eskom_stage ORDER BY ROWID DESC LIMIT 1')
        old_stage = cursor.fetchone()
        old_stage = old_stage[0] if old_stage else old_stage
        if stage != old_stage:
            cursor.execute('INSERT INTO eskom_stage(stage) VALUES (?)', (stage,))
            self.con.commit()
            await self.announce_stage_change(cursor=cursor, stage=str(stage))
        cursor.close()

    def init_cogs(self):
        """ Add cogs to bot """
        for cog in self.cogs:
            self.bot.add_cog(cog['obj'](self.bot))

    async def on_ready(self):
        """ Print to console once bot is connected """
        print(f'{self.bot.user.name} is connected.')

    def add_events(self):
        """ Add events to bot """
        self.bot.event(self.on_ready)

    def start_bot(self):
        """ Run long running loop task and then start up the bot """
        # pylint: disable=E1101
        self.lookup_eskom_stage.start()
        self.bot.run(self.token)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Eskom discord bot.')
    parser.add_argument('-t', '--token', type=str, help='Use discord token for bot.')
    args = parser.parse_args()
    client = Deskom(token=args.token)
    client.start_bot()
