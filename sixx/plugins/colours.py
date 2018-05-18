from curious.commands import Plugin
from ruamel.yaml import YAML


def load_colours():
    yaml = YAML()

    with open('sixx/data/colours.yml', 'r') as f:
        return yaml.load(f)


class Colours(Plugin):
    """
    Colour related commands.
    """
    colours = load_colours()
