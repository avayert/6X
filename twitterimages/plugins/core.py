from operator import methodcaller

from curio import subprocess
from curious import Embed
from curious.commands import Plugin, command

from twitterimages.plugins.utils.decorators import is_owner


class Core(Plugin):
    """
    Core commands for the bot.
    """

    @command()
    @is_owner()
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
    @is_owner()
    async def quit(self, ctx):
        """
        Disconnects the bot from Discord.
        """
        # TODO don't hard-code the emote
        await ctx.channel.messages.send('<:exit:421816310909894670> Shutting down...')
        await self.client.kill()

    @command()
    async def changelog(self, ctx, amount: int = 3):
        """
        Shows the latest changes in the git repository.
        """
        amount = max(min(10, amount), 1)
        process = subprocess.Popen(f'git log -n {amount}'.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = map(methodcaller('decode'), await process.communicate())

        await ctx.channel.messages.send(f'```{stdout}```')
