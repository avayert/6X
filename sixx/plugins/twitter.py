import curio
import logging
import re
from curious import event, EventContext
from curious.commands import Plugin
from curious.exc import NotFound

from sixx.plugins.utils import twitter
from sixx.plugins.utils.twitter import TweetEmbed

# ide-noformat
tweet_pattern = re.compile(r'(?P<before>^|\s)'   # Match start of string or whitespace
                           r'(?P<url>https?://'  # Starts a capture group `url` 
                           r'(?:mobile\.)?'      # Mobile links start with "mobile."
                           r'twitter\.com/\S+/'  # Match "twitter.com/username/"
                           r'(?P<id>\d+))'       # Match the twitter status ID
                           r'(?:\?.*?=.*?)*'     # Ignores URL parameters (most common is ?s=num)
                           r'(?P<after>$|\s)'    # Match end of string or whitespace
                           )
# ide-format
all_but_first = slice(1, None, None)

logger = logging.getLogger('6X')


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
            tweet = await twitter.get_tweet(tweet_match.group('id'))
        except ValueError:
            logger.exception('ValueError raised in parse_tweets')
            return

        media = tweet.get('extended_entities', {}).get('media', [])
        images = media[all_but_first]
        author = message.author

        embed = twitter.build_embed(tweet, author, media)

        try:
            async with curio.TaskGroup() as group:
                def replace(match):
                    before, after, url = [match.group(name) for name in 'before after url'.split()]
                    return f'{before}<{url}>{after}'

                await group.spawn(message.delete())
                await group.spawn(
                    message.channel.messages.send(tweet_pattern.sub(replace, message.content),
                                                  embed=embed))
        except curio.TaskGroupError as e:
            ignore = (NotFound,)

            for error in e.errors:
                if error in ignore:
                    continue
                logger.error(f'Unhandled exception: {e}')

        embed = TweetEmbed.from_member(author)
        for image in images:
            embed.set_image(image_url=image['media_url_https'])
            await message.channel.messages.send(embed=embed)

        if tweet['is_quote_status']:
            quoted_tweet = tweet['quoted_status']
            embed = twitter.build_embed(quoted_tweet, author)

            await message.channel.messages.send('Quoted tweet:', embed=embed)
