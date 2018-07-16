import curio
import logging
import re
from curious import event, EventContext, Embed
from curious.commands import Plugin

from sixx.plugins.utils import twitter

tweet_pattern = re.compile(r'(?:^|\W)https?://(?:mobile\.)?twitter\.com/\S+/(\d+)(?:$|\W)')
tweet_fmt = 'https://twitter.com/{0[user][screen_name]}/status/{0[id]}'

all_but_first = slice(1, None, None)

logger = logging.getLogger('TwitterImages')


class Twitter(Plugin):
    """
    Plugin for all Twitter related commands and events.
    """

    @event('message_create')
    async def parse_tweets(self, ctx: EventContext, message):
        """
        Tries to find all tweets withing a message and post information about them.
        """
        if message.author.user.bot:
            return

        tweet_match = tweet_pattern.search(message.content)

        if tweet_match is None:
            return

        try:
            tweet = await twitter.get_tweet(tweet_match.group(1))
        except ValueError:
            logger.exception('ValueError raised in parse_tweets')
            return

        media = tweet.get('extended_entities', {}).get('media', [])
        images = media[all_but_first]

        embed = twitter.build_embed(tweet, media)
        embed.set_footer(text='Posted to discord by {0.name}'.format(message.author),
                         icon_url=str(message.author.user.avatar_url))
        embed.colour = message.author.colour

        async with curio.TaskGroup() as group:
            # TODO escape markdown in username
            await group.spawn(message.delete())
            await group.spawn(
                message.channel.messages.send(f'<{tweet_match.group(0)}>', embed=embed))

        embed = Embed()
        embed.set_footer(text='Posted to Discord by {0.name}'.format(message.author),
                         icon_url=str(message.author.user.avatar_url))
        embed.colour = message.author.colour

        for image in images:
            embed.set_image(image_url=image['media_url_https'])
            await message.channel.messages.send(embed=embed)

        if tweet['is_quote_status']:
            await message.channel.messages.send(tweet_fmt.format(tweet['quoted_status']))
