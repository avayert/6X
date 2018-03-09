import re

import asks
import multio
from curious.core.client import Client

from credentials import discord, twitter

multio.init('curio')

client = Client(discord.token)
tweet_pattern = re.compile(r'https?://twitter.com/\S+/(\d+)')


async def get_tweet(id):
    resp = await asks.get(
        'https://api.twitter.com/1.1/statuses/show.json',
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

        # This is awful please ignore it
        reply = tweet['in_reply_to_status_id']
        if reply:
            replied_to = await get_tweet(reply)

            fmt = 'https://twitter.com/{0[user][screen_name]}/status/{0[id]}'
            await message.channel.messages.send(fmt.format(replied_to))


if __name__ == '__main__':
    client.run()
