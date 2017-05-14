#!/usr/bin/python

# ved2json.py
#   by Mike Melanson (mike -at- multimedia.cx)

# Export the text strings from a Visionaire .ved XML file into a JSON file.
#
# USAGE: ved2json.py input.ved strings.json

import json
import sys
import xml.etree.ElementTree as ET

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "USAGE: %s input.ved output.json" % (sys.argv[0])
        sys.exit(1)

    string_list = []
    string_set = set()
    string_count = 0
    in_tree = ET.parse(sys.argv[1])
    in_root = in_tree.getroot()
    texts = in_root.find('Texts')
    for text_elem in texts:
        text_langs_elem = text_elem.find('TextTextLanguages')
        if text_langs_elem is None:
            continue
        for text in text_langs_elem:
            unicode_string = text.get('Text').encode('utf-8')
            if len(unicode_string) > 0 and unicode_string not in string_set:
                pair = { 'original': unicode_string,
                         'translated': unicode_string }
                string_list.append(pair)
                string_set.add(unicode_string)

open(sys.argv[2], "w").write(json.dumps(string_list, indent=4, ensure_ascii=False))
