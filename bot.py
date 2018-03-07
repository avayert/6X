import re

import asks
from curious.core.client import Client
import multio

from credentials import discord, twitter


multio.init('curio')

client = Client(discord.token)
tweet_pattern = re.compile(r'https?://twitter.com/\S+/(\d+)')


def get_tweet(id):
    return asks.get(
        'https://api.twitter.com/1.1/statuses/show.json',
        headers={'Authorization': twitter.token},
        params={'id': id}
    )


@client.event('message_create')
async def parse_tweets(ctx, message):
    if message.author.user.bot:
        return

    for tweet in tweet_pattern.finditer(message.content):
        resp = await get_tweet(tweet.group(1))
        tweet = resp.json()

        # Ignore first images because discord should show it
        images = tweet.get('extended_entities', {'media': []})['media'][1:]

        for image in images:
            await message.channel.messages.send(image['media_url_https'])


if __name__ == '__main__':
    client.run()
