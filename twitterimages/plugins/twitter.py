import asks
import logging
import re
from curious import event
from curious.commands import Context, Plugin

from twitterimages.credentials import twitter

tweet_pattern = re.compile(r'(?:^|\W)https?://(?:mobile\.)?twitter\.com/\S+/(\d+)(?:$|\W)')
tweet_fmt = 'https://twitter.com/{0[user][screen_name]}/status/{0[id]}'

all_but_first = slice(1, None, None)

logger = logging.getLogger('TwitterImages')


class Twitter(Plugin):
    """
    Plugin for all Twitter related commands and events.
    """

    @staticmethod
    async def get_tweet(id: str) -> dict:
        """
        Uses the twitter API to get a tweet with a corresponding ID.

        :param id: The ID of the tweet being searched.
        :return: JSON data returned by the twitter API.
        """
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

    @event('message_create')
    async def parse_tweets(self, ctx: Context, message):
        """
        Tries to find all tweets withing a message and post information about them.
        """
        if message.author.user.bot:
            return

        for tweet in tweet_pattern.finditer(message.content):
            try:
                tweet = await self.get_tweet(tweet.group(1))
            except ValueError:
                logger.exception('ValueError raised in parse_tweets')
                continue

            media = tweet.get('extended_entities', {}).get('media', [])
            images = media[all_but_first]

            for image in images:
                await message.channel.messages.send(image['media_url_https'])

            if tweet['is_quote_status']:
                await message.channel.messages.send(tweet_fmt.format(tweet['quoted_status']))
