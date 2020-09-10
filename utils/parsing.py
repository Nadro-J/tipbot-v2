import re, json, os

def dump_json(filename, data):
    try:
        with open(filename, 'w') as f:
            decode_jdata = json.dumps(json.JSONDecoder().decode(data))
            reload = json.loads(decode_jdata)
            json.dump(reload, f, indent=4)
    except Exception as e:
        print (e)

def load_json(path):
    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)

def parse2json(data):
    return json.dumps(data, indent=4)

def check_duplicate(item, list):
    if item in list:
        return True
    else:
        return False

def parse_json(filename):
    """ remove //-- and /* -- */ style comments from JSON """
    comment_re = re.compile('(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?', re.DOTALL | re.MULTILINE)
    with open(filename) as f:
        content = f.read()
        match = comment_re.search(content)
        while match:
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)

        contents = json.loads(content)

    if 'data' in contents:
        # Backwards compatible with old config.json files
        contents = contents['data'][0]

    return contents
