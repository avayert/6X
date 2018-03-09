import re

import asks
import multio
from contextlib import suppress

from curio import subprocess
from curious import Embed
from curious.commands import CommandsManager, command
from curious.core.client import Client
from operator import methodcaller

from twitterimages.credentials import discord, twitter

multio.init('curio')

client = Client(discord.token)
manager = CommandsManager.with_client(client, command_prefix='t!')

tweet_pattern = re.compile(r'https?://twitter.com/\S+/(\d+)')
tweet_fmt = 'https://twitter.com/{0[user][screen_name]}/status/{0[id]}'


@command()
async def update(ctx):
    # TODO maybe allow arguments for better control (using argparse?)
    process = subprocess.Popen('git pull'.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = map(methodcaller('decode'), await process.communicate())

    # TODO output might be over 2000 characters...?
    description = '```diff\n{0}\n{1}```'.format(stdout, stderr)
    # relies on there not being both stdout and stderr output, let's see
    embed = Embed(colour=0xcc0000 if stderr else 0x4BB543, description=description)

    await ctx.channel.messages.send(embed=embed)

manager.add_command(update)


async def get_tweet(id):
    resp = await asks.get(
        uri='https://api.twitter.com/1.1/statuses/show.json',
        headers={'Authorization': twitter.token},
        params={'id': id}
    )
    return resp.json()


@client.event('message_create')
async def parse_tweets(ctx, message):
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


if __name__ == '__main__':
    client.run()
