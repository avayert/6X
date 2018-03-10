import re
from contextlib import suppress

import asks
import curio
import multio
from curious.commands import CommandsManager
from curious.core.client import Client

from twitterimages.credentials import discord, twitter

multio.init('curio')

client = Client(discord.token)
manager = CommandsManager.with_client(client, command_prefix='t!')

tweet_pattern = re.compile(r'https?://twitter.com/\S+/(\d+)')
tweet_fmt = 'https://twitter.com/{0[user][screen_name]}/status/{0[id]}'


async def get_tweet(id):
    resp = await asks.get(
        uri='https://api.twitter.com/1.1/statuses/show.json',
        headers={'Authorization': twitter.token},
        params={'id': id}
    )
    return resp.json()


@client.event('message_create')
async def parse_tweets(ctx, message):
    # TODO maybe move this to a fitting plugin later
    if message.author.user.bot:
        return

    for tweet in tweet_pattern.finditer(message.content):
        tweet = await get_tweet(tweet.group(1))

        # Ignore first images because discord should show it
        images = tweet.get('extended_entities', {'media': []})['media'][1:]

        for image in images:
            await message.channel.messages.send(image['media_url_https'])

        if tweet['is_quote_status']:
            await message.channel.messages.send(tweet_fmt.format(tweet['quoted_status']))

        with suppress(KeyError):
            replied_to = await get_tweet(tweet['in_reply_to_status_id'])
            await message.channel.messages.send(tweet_fmt.format(replied_to))


async def main():
    await manager.load_plugins_from('plugins.core')

    await client.run_async()


if __name__ == '__main__':
    curio.run(main)
