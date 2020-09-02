import re, json

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
