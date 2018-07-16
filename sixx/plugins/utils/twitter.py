from collections import namedtuple

import asks
import curious
import re

from sixx.credentials import twitter

format_map = namedtuple('fmt', 'fmt attr_name')


def fix_content(tweet):
    content = tweet['full_text']
    offset = 0
    entities = []

    for entity_type, entries in tweet['entities'].items():
        # TODO handle this in the future I don't care enough right now
        if entity_type == 'symbols':
            continue
        for entry in entries:
            entry.update(entity_type=entity_type)
            entities.append(entry)

    formats = {
        'hashtags': format_map('[#{0}](https://twitter.com/hashtag/{0})', 'text'),
        'user_mentions': format_map('[@{0}](https://twitter.com/{0})', 'screen_name'),
        'urls': format_map('{0}', 'expanded_url'),
        'media': format_map('', 'url')
    }

    for entry in sorted(entities, key=lambda e: e['indices']):
        start, end = map(lambda index: index + offset, entry['indices'])

        fm = formats[entry['entity_type']]
        new = fm.fmt.format(entry[fm.attr_name])

        content = content[:start] + new + content[end:]
        offset += len(new) - (end - start)
    return content


def build_embed(tweet, media):
    user = tweet['user']
    base = 'https://twitter.com/{0[screen_name]}'.format(user)

    embed = curious.Embed(description=fix_content(tweet), url=base + '/status/' + tweet['id_str'])

    embed.set_author(url=base, icon_url=user['profile_image_url_https'],
                     name='{0[name]} ({0[screen_name]})'.format(user))

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

    errors = json.get('errors')
    if errors:
        message = ' '.join('Code {code} {message}'.format(**error) for error in errors)
        raise ValueError(message)
    else:
        return json
