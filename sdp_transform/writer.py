from .grammar import grammar


def makeLine(field, obj, location):
    string = field + '=' + (obj['format']((location if obj.get('push') else location[obj.get('name')])) if callable(obj['format']) else obj['format'])
    args = []
    if obj.get('names'):
        for name in obj.get('names'):
            if obj.get('name'):
                if location[obj.get('name')].get(name) != None:
                    args.append(location[obj.get('name')][name])
            else:
                if location.get(name) != None:
                    args.append(location[name])
    else:
        args.append(location[obj.get('name')])
    
    return string % tuple(args)


defaultOuterOrder = [
  'v', 'o', 's', 'i',
  'u', 'e', 'p', 'c',
  'b', 't', 'r', 'z', 'a'
]

defaultInnerOrder = ['i', 'c', 'b', 'a']

def write(session: dict, outerOrder: list=defaultOuterOrder, innerOrder:list=defaultInnerOrder):
    if session.get('version') == None:
        session['version'] = 0 # 'v=0' must be there (only defined version atm)
    if session.get('name') == None:
        session['name'] = ' ' # 's= ' must be there if no meaningful name set

    for media in session.get('media',[]):
        if media.get('payloads') == None:
            media.payloads = ''
    
    sdp = []

    # loop through outerOrder for matching properties on session
    for field in outerOrder:
        for obj in grammar[field]:
            if obj.get('name'):
                if obj['name'] in session.keys():
                    if session.get(obj['name']) != None:
                        sdp.append(makeLine(field, obj, session))
            elif obj.get('push'):
                if obj['push'] in session.keys():
                    if session.get(obj['push']) != None:
                        for el in session.get(obj['push']):
                            sdp.append(makeLine(field, obj, el))
    
    # then for each media line, follow the innerOrder
    for mLine in session.get('media', []):
        sdp.append(makeLine('m', grammar['m'][0], mLine))

        for field in innerOrder:
            for obj in grammar[field]:
                if obj.get('name'):
                    if obj['name'] in mLine.keys():
                        if mLine.get(obj['name']) != None:
                            sdp.append(makeLine(field, obj, mLine))
                elif obj.get('push'):
                    if obj['push'] in mLine.keys():
                        if mLine.get(obj['push']) != None:
                            for el in mLine.get(obj['push']):
                                sdp.append(makeLine(field, obj, el))

    return '\r\n'.join(sdp)
