import re

from curious.core.client import Client
import multio

from credentials import discord


multio.init('curio')

client = Client(discord.token)
tweet_pattern = re.compile(r'https?://twitter.com/\S+/\d+')


@client.event('message_create')
async def parse_tweets(ctx, message):
    if message.author.user.bot:
        return

    for tweet in tweet_pattern.findall(message.content):
        await message.channel.messages.send(tweet)


if __name__ == '__main__':
    client.run()
