import asks
import curio
import curious
import logging
import re
from curious import event, EventContext, Embed
from curious.commands import Plugin

from sixx.credentials import twitter

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
            params={'id': id, 'tweet_mode': 'extended'}  # Holy SHIT the twitter API sucks,,,,,
        )
        json = resp.json()

        errors = json.get('errors')
        if errors:
            message = ' '.join('Code {code} {message}'.format(**error) for error in errors)
            raise ValueError(message)
        else:
            return json

    @staticmethod
    def build_embed(tweet, media):
        user = tweet['user']
        base = 'https://twitter.com/{0[screen_name]}'.format(user)
        text = re.sub(r'({})'.format('|'.join(image['url'] for image in media)), '', tweet['full_text'])

        embed = curious.Embed(description=text, url=base + '/status/' + tweet['id_str'])

        embed.set_footer(text='Twitter', icon_url='https://abs.twimg.com/icons/apple-touch-icon-192x192.png')

        embed.set_author(url=base, icon_url=user['profile_image_url_https'],
                         name='{0[name]} ({0[screen_name]})'.format(user))

        if media:
            embed.set_image(image_url=media[0]['media_url_https'])

        return embed

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
            tweet = await self.get_tweet(tweet_match.group(1))
        except ValueError:
            logger.exception('ValueError raised in parse_tweets')
            return

        media = tweet.get('extended_entities', {}).get('media', [])
        images = media[all_but_first]

        embed = self.build_embed(tweet, media)

        async with curio.TaskGroup() as group:
            # TODO escape markdown in username
            await group.spawn(message.delete())
            await group.spawn(
                message.channel.messages.send('**{0.author.name}**: <{1}>'.format(message, tweet_match.group(0)),
                                              embed=embed))

        embed = Embed()
        embed.set_footer(text='Twitter', icon_url='https://abs.twimg.com/icons/apple-touch-icon-192x192.png')

        for image in images:
            embed.set_image(image_url=image['media_url_https'])
            await message.channel.messages.send(embed=embed)

        if tweet['is_quote_status']:
            await message.channel.messages.send(tweet_fmt.format(tweet['quoted_status']))
