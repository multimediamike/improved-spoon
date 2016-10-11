#!/usr/bin/python

# ldt2json.py
#  by Mike Melanson (mike -at- multimedia.cx)

import json
import struct
import sys

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "USAGE: ldt2json.py <file.ldt> <key> <file.json>"
        sys.exit(1)
    output_json = sys.argv[3]

    # process the key
    key = sys.argv[2]
    key_len = len(key)
    print "Using key '%s' (is this what you entered on the command line?)" % (key)
    key_table = []
    for k in key:
        key_table.append(ord(k))

    # read and decrypt the data
    ldt = open(sys.argv[1], "rb").read()
    utf16_bytes = ""
    for i in xrange(len(ldt)):
        enc_byte = struct.unpack("B", ldt[i])[0]
        dec_byte = enc_byte - key_table[i % key_len]
        if dec_byte < 0:
            dec_byte = 256 + dec_byte
        try:
            utf16_bytes += struct.pack("B", dec_byte)
        except struct.error:
            print "Error encountered while decoding; is the key correct?"
            sys.exit(1)
    utf16_string = utf16_bytes.decode("utf-16-le")
    utf8_string = utf16_string.encode("utf-8")

    # Format of a subtitle in the LDT file:
    #  Timestamp<!>Duration<!><!>Subtitle<!>
    # The timestamp and duration fields are floating point numbers expressed
    # as text and represent seconds. The subtitle text is surrounded by the
    # <!>. Thus, by splitting the string on '<!>', there are 4 components
    # per subtitle.
    ldt_parts = utf8_string.split("<!>")

    # total number of parts should be 4 per string, plus 1 due to the
    # vagaries of string splitting
    if (len(ldt_parts) - 1) % 4 != 0:
        print "Invalid number of parts in the file (%d)" % len(ldt_parts)
        sys.exit(1)

    # create an array of subtitle data
    subtitles = []
    for i in xrange((len(ldt_parts) - 1) / 4):
        timestamp = ldt_parts[i*4+0]
        duration = ldt_parts[i*4+1]
        subtitle = ldt_parts[i*4+3]
        subtitles.append({
            'timestamp': timestamp,
            'duration': duration,
            'original': subtitle,
            'translated': subtitle
        })

    # write the subtitle data to a JSON file to be translated
    print "dumping strings to '%s'" % (output_json)
    open(output_json, "w").write(json.dumps(subtitles, indent=4))
