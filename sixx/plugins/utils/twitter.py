import asks
import logging
from curious import Embed, Member

from sixx.credentials import twitter

logger = logging.getLogger('6X')


class TweetEmbed(Embed):
    @classmethod
    def from_member(cls, member: Member):
        embed = cls(colour=member.colour)
        embed.set_footer(text='Posted to Discord by {0.name}'.format(member),
                         icon_url=str(member.user.avatar_url.as_format('png')))
        return embed


def fix_content(tweet):
    content = tweet['full_text']
    offset = 0

    entities = [
        {**items, 'entity_type': entity_type}
        for entity_type, entities in tweet['entities'].items()
        for items in entities
    ]

    formats = {
        'user_mentions': ('[@{0}](https://twitter.com/{0})', 'screen_name'),
        'hashtags': ('[#{0}](https://twitter.com/hashtag/{0})', 'text'),
        'urls': ('{0}', 'expanded_url'),
        'media': ('', 'url')
    }

    for entry in sorted(entities, key=lambda e: e['indices']):
        start, end = entry['indices']
        entity_type = entry['entity_type']

        fmt, attr = formats.get(entity_type, (None, None))

        if fmt is None:
            logger.warning(f'Unhandled entity type: {entity_type}')
            continue

        replacement = fmt.format(entry[attr])

        content = content[:start + offset] + replacement + content[end + offset:]

        offset += len(replacement) - (end - start)

    return content


def build_embed(tweet, author, media=None):
    if media is None:
        media = tweet.get('extended_entities', {}).get('media', [])

    user = tweet['user']
    base = 'https://twitter.com/{0[screen_name]}'.format(user)

    embed = TweetEmbed.from_member(author)
    embed.description = fix_content(tweet)
    embed.url = base + '/status/' + tweet['id_str']

    embed.set_author(url=base, icon_url=user['profile_image_url_https'],
                     name='{0[name]} (@{0[screen_name]})'.format(user))

    embed.add_field(name='Retweets', value=tweet['retweet_count'])
    embed.add_field(name='Likes', value=tweet['favorite_count'])

    if media:
        embed.set_image(image_url=media[0]['media_url_https'])

    return embed


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

    logger.debug(f'Twitter API response for tweet id {id}: {json}')

    errors = json.get('errors')
    if errors:
        message = ' '.join('Code {code} {message}'.format(**error) for error in errors)
        raise ValueError(message)
    else:
        return json
