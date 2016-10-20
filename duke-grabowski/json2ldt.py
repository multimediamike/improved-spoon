#!/usr/bin/python

# json2ldt.py
#  by Mike Melanson (mike -at- multimedia.cx)

import json
import struct
import sys

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "USAGE: <file.json> <key> <file.ldt>"
        sys.exit(1)
    out_ldt = sys.argv[3]

    # process the key
    key = sys.argv[2]
    key_len = len(key)
    print "Using key '%s' (is this what you entered on the command line?)" % (key)
    key_table = []
    for k in key:
        key_table.append(ord(k))

    # load the translated subtitles and rebuild the LDT file format;
    # use UTF-8 for this phase
    subtitles = json.loads(open(sys.argv[1], "r").read())
    translated = u""
    for subtitle in subtitles:
        translated += subtitle[0]['timestamp']
        translated += "<!>"
        translated += subtitle[1]['duration']
        translated += "<!>"
        translated += subtitle[3]['translated_1']
        translated += "<!>"
        translated += subtitle[5]['translated_2']
        translated += "<!>"

    # convert UTF-8 string to UTF-16 that C# likes
    utf16_string = translated.encode("utf-16-le")

    # Write the data to a tempfile and re-read it as binary (don't know a
    # way to convert UTF-16 string to binary string otherwise). Use the
    # specifed output file as a temporary file instead of a proper Python
    # tempfile so that Windows doesn't have to read from an open writable
    # file.
    open(out_ldt, "wb").write(utf16_string)
    bin_string = open(out_ldt, "rb").read()
    enc_string = ""
    for i in xrange(len(bin_string)):
        byte = struct.unpack("B", bin_string[i])[0]
        enc_byte = (byte + key_table[i % key_len]) % 256
        enc_string += struct.pack("B", enc_byte)

    # write the final, encrypted output
    print "creating new LDT file '%s'" % (out_ldt)
    open(out_ldt, "wb").write(enc_string)
