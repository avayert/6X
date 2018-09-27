import curio
import random
import re
from curious import event, Guild
from curious.commands import Plugin, command, Context


class Miscellaneous(Plugin):
    def __init__(self, client):
        super().__init__(client)

        # https://thehardtimes.net/harddrive/we-came-up-with-nicknames-for-waluigi/
        with open('sixx/data/waluigi.txt', 'r') as f:
            self.waluigis = f.read().splitlines()

        self.waluigi_task = None

    async def load(self):
        self.waluigi_task = await curio.spawn(self.waluigi_event)

    async def unload(self):
        if self.waluigi_task is not None:
            await self.waluigi_task.cancel()

    @command()
    async def waluigi(self, ctx: Context):
        await ctx.channel.messages.send(random.choice(self.waluigis))

    async def waluigi_event(self):
        guild = self.client.guilds.get(198101180180594688)
        channel = guild.system_channel

        while True:
            seconds = random.randint(60 * 60, 60 * 60 * 18)
            await curio.sleep(seconds)

            message = 'Wah! Wah! ' + random.choice(self.waluigis)
            with open('sixx/data/wah.jpg', 'rb') as f:
                await channel.messages.upload(f, filename='wah.jpg', message_content=message)

    @event('guild_update')
    async def watch_guild_name(self, ctx, old: Guild, new: Guild):
        if old.id != 198101180180594688:
            return

        if old.name == new.name:
            return

        def escape(name):
            return re.sub(r'([*`_~\\])', r'\\\1', name)

        old_name, new_name = [escape(guild.name) for guild in (old, new)]
        await new.system_channel.messages.send(f'"{old_name}" is now called "**{new_name}**"')
