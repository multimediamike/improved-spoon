#!/usr/bin/python

# sentence.bin2json.py
#  by Mike Melanson (mike -at- multimedia.cx)

import json
import struct
import sys

HEADER_BYTE_COUNT = 17

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "USAGE: sentence.bin2json.py <sentence.bin> <sentence.bin.json>"
        sys.exit(1)

    infilename = sys.argv[1]
    outfilename = sys.argv[2]

    sentence = open(infilename, "rb").read()
    sentence_len = len(sentence)

    header_bytes = []
    for i in xrange(HEADER_BYTE_COUNT):
        header_bytes.append(struct.unpack("B", sentence[i])[0])

    i = HEADER_BYTE_COUNT
    strings = []
    while i < sentence_len:
        str_len = struct.unpack("<I", sentence[i:i+4])[0]
        i += 4
        string = sentence[i:i+str_len].decode("latin-1").encode("utf-8")
        i += str_len
        strings.append( { 'original': string, 'translated': string } )

    output_dictionary = {
        'header_bytes_do_not_modify': header_bytes,
        'strings': strings
    }

    print "dumping strings from '%s' -> '%s'" % (infilename, outfilename)
    open(outfilename, "wb").write(json.dumps(output_dictionary, indent=4, ensure_ascii=False))
