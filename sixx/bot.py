import logging
import multio
from curious import EventContext
from curious.commands import CommandsManager, Context
from curious.commands.exc import ConditionsFailedError, ConversionFailedError
from curious.core.client import Client
from pathlib import Path

from sixx.credentials import discord

multio.init('curio')

client = Client(discord.token)
manager = CommandsManager.with_client(client, command_prefix='t!')
client.manager = manager

logger = logging.getLogger('6X')


@client.event('command_error')
async def handle_errors(event_ctx: EventContext, ctx: Context, error):
    if isinstance(error, ConditionsFailedError):
        logger.info(
            '{author.name}#{author.discriminator} ({author.user.id}) '
            'Tried to use the command `{0.command_name}`'
            .format(ctx, error, author=ctx.author.user)
        )
        return
    if isinstance(error, ConversionFailedError):
        await ctx.channel.messages.send(str(error))

    raise error


async def main():
    plugins = Path('./sixx/plugins').glob('*.py')

    for plugin in plugins:
        await manager.load_plugins_from('sixx.plugins.' + plugin.stem)

    await client.run_async()
