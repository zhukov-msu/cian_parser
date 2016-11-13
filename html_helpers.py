import re


def html_stripper(text):
    return re.sub('<[^<]+?>', '', str(text))
