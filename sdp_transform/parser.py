import re
from functools import reduce

from .grammar import grammar


def toIntIfInt(v):
    try:
        return int(v)
    except ValueError:
        return v

def attachProperties(match, location, names=None, rawName=None):
    if rawName and not names:
        location[rawName] = toIntIfInt(match[1])
    else:
        i = 0
        while i < len(names):
            if match[i + 1] != None:
                location[names[i]] = toIntIfInt(match[i + 1])
            i += 1
    return

def parseReg(obj, location, content):
    needsBlank = obj.get('name') and obj.get('names')
    if obj.get('push'):
        if not location.get(obj.get('push')):
            location[obj.get('push')] = []

    elif needsBlank:
        if not location.get(obj.get('name')):
            location[obj.get('name')] = {}
    keyLocation = {} if obj.get('push') else (
        location.get(obj.get('name')) if needsBlank else location)

    attachProperties(re.match(obj['reg'], content),
                     keyLocation, obj.get('names'), obj.get('name'))

    if obj.get('push'):
        location[obj.get('push')].append(keyLocation)

def parse(sdp: str) -> dict:
    session = {}
    media = []
    location = session
    lines = [line for line in sdp.splitlines(
    ) if re.match(r'^([a-z])=(.*)', line)]
    for l in lines:
        field = l[0]
        content = l[2:]

        if field == 'm':
            media.append({
                'rtp': [],
                'fmtp': []
            })
            location = media[-1]

        for obj in grammar[field]:
            if re.match(obj['reg'], content):
                parseReg(obj, location, content)
                break

    session['media'] = media
    return session

def paramReducer(acc, expr):
    s = expr.split('=')
    if len(s) == 2:
        acc[s[0]] = toIntIfInt(s[1])
    elif len(s) == 1 and len(expr) > 1:
        acc[s[0]] = None
    return acc

def parseParams(string: str):
    return reduce(paramReducer, re.split(r';\s?', string), {})
