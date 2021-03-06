#!/usr/bin/python

# json2ved.py
#   by Mike Melanson (mike -at- multimedia.cx)

# Create a new .ved XML file based on an original .ved file as well as
# a JSON file filled with strings (generated by ved2json.py and possibly
# translated to a new language).
#
# USAGE: json2ved.py strings.json input.ved output.ved

import json
import sys
import xml.etree.ElementTree as ET

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "USAGE: %s strings.json input.ved output.ved" % (sys.argv[0])
        sys.exit(1)

    # load the strings from the input JSON file
    input_strings_array = json.loads(open(sys.argv[1], "r").read())
    input_strings_dict = {}
    for pair in input_strings_array:
        input_strings_dict[pair['original']] = pair['translated']

    # load and parse the XML
    in_tree = ET.parse(sys.argv[2])
    in_root = in_tree.getroot()
    texts = in_root.find('Texts')
    for text_elem in texts:
        text_langs_elem = text_elem.find('TextTextLanguages')
        if text_langs_elem is None:
            continue
        for text in text_langs_elem:
            unicode_string = text.attrib['Text'].encode('utf-8')
            if len(unicode_string) > 0 and unicode_string in input_strings_dict:
                text.attrib['Text'] = input_strings_dict[unicode_string]

    # write the new XML file
    in_tree.write(sys.argv[3], encoding="utf8", xml_declaration=True)
