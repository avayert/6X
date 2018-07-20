import curio
import random
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
        await self.client.wait_for('ready')

        channel = self.client.find_channel(348933705923952641)

        while True:
            seconds = random.randint(60 * 60, 60 * 60 * 18)
            await curio.sleep(seconds)

            message = 'Wah! Wah! ' + random.choice(self.waluigis)
            with open('sixx/data/wah.jpg', 'rb') as f:
                await channel.messages.upload(f, filename='wah.jpg', message_content=message)
