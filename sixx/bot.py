import logging
import multio
from curious import EventContext
from curious.commands import CommandsManager, Context
from curious.commands.exc import ConditionsFailedError
from curious.core.client import Client

from sixx.credentials import discord

multio.init('curio')

client = Client(discord.token)
manager = CommandsManager.with_client(client, command_prefix='t!')

logger = logging.getLogger('TwitterImages')


@client.event('command_error')
async def silence_condition_failure(event_ctx: EventContext, ctx: Context, error):
    if isinstance(error, ConditionsFailedError):
        logger.info(
            '{author.name}#{author.discriminator} ({author.user.id}) '
            'Tried to use the command `{0.command_name}`'
            .format(ctx, error, author=ctx.author.user)
        )
        return

    raise error


async def main():
    await manager.load_plugins_from('sixx.plugins.core')
    await manager.load_plugins_from('sixx.plugins.twitter')

    await client.run_async()
