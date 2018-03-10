from operator import methodcaller

from curio import subprocess
from curious import Embed
from curious.commands import Plugin, command


class Core(Plugin):
    """
    Core commands for the bot.
    """

    @command()
    async def update(self, ctx):
        """
        Downloads the latest version of the bot.

        The command does not change the state of the current running bot.
        In order for the changes to apply, the files and/or the bot have to be reloaded.
        """
        # TODO maybe allow arguments for better control (using argparse?)
        process = subprocess.Popen('git pull'.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = map(methodcaller('decode'), await process.communicate())

        # TODO output might be over 2000 characters...?
        description = '```diff\n{0}\n{1}```'.format(stdout, stderr)
        # TODO relies on there not being both stdout stderr output,
        embed = Embed(colour=0xcc0000 if stderr else 0x4BB543, description=description)
        embed.set_author(
            name='Result:',
            url='https://github.com/TildeBeta/TwitterImages',
            icon_url='https://cdn.discordapp.com/emojis/421819534060814347.png?v=1'
        )

        await ctx.channel.messages.send(embed=embed)

    @command(aliases='exit kill shutdown'.split())
    async def quit(self, ctx):
        """
        Disconnects the bot from Discord.
        """
        # TODO don't hard-code the emote
        await ctx.channel.messages.send('<:exit:421816310909894670> Shutting down...')
        await self.client.kill()
