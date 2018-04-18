import logging
import re

import asks
import multio
from curious.commands import CommandsManager, Context
from curious.commands.exc import ConditionsFailedError
from curious.core.client import Client

from twitterimages.credentials import discord, twitter

multio.init('curio')

client = Client(discord.token)
manager = CommandsManager.with_client(client, command_prefix='t!')

logger = logging.getLogger('TwitterImages')

tweet_pattern = re.compile(r'(?:^|\W)https?://(?:mobile\.)?twitter\.com/\S+/(\d+)(?:$|\W)')
tweet_fmt = 'https://twitter.com/{0[user][screen_name]}/status/{0[id]}'


async def get_tweet(id):
    resp = await asks.get(
        uri='https://api.twitter.com/1.1/statuses/show.json',
        headers={'Authorization': twitter.token},
        params={'id': id}
    )
    json = resp.json()

    errors = json.get('errors')
    if errors:
        message = ' '.join('Code {code} {message}'.format(**error) for error in errors)
        raise ValueError(message)
    else:
        return json


@client.event('message_create')
async def parse_tweets(ctx, message):
    # TODO maybe move this to a fitting plugin later
    if message.author.user.bot:
        return

    for tweet in tweet_pattern.finditer(message.content):
        try:
            tweet = await get_tweet(tweet.group(1))
        except ValueError:
            logger.exception('ValueError raised in parse_tweets')
            continue

        # Ignore first images because discord should show it
        images = tweet.get('extended_entities', {'media': []})['media'][1:]

        for image in images:
            await message.channel.messages.send(image['media_url_https'])

        if tweet['is_quote_status']:
            await message.channel.messages.send(tweet_fmt.format(tweet['quoted_status']))


@client.event('command_error')
async def silence_condition_failure(event_ctx, ctx, error):
    if isinstance(error, ConditionsFailedError):
        logging.info(
            '{author.name}#{author.discriminator} ({author.user.id}) '
            'Tried to use the command `{0.command_name}`'
            .format(ctx, error, author=ctx.author.user)
        )
        return

    raise error


async def main():
    await manager.load_plugins_from('twitterimages.plugins.core')

    await client.run_async()
