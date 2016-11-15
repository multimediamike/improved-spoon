#!/usr/bin/python

# json2sentence.bin.py
#  by Mike Melanson (mike -at- multimedia.cx)

import json
import struct
import sys

HEADER_BYTE_COUNT = 17

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "USAGE: json2sentence.bin.py <sentence.bin.json> <new-sentence.bin>"
        sys.exit(1)

    infilename = sys.argv[1]
    outfilename = sys.argv[2]

    print "repacking data from '%s' -> '%s'" % (infilename, outfilename)

    input_dict = json.loads(open(infilename, "rb").read())
    header_bytes = input_dict['header_bytes_do_not_modify']
    strings = input_dict['strings']

    outfile = open(outfilename, "wb")

    # write the header
    header = ""
    for byte in header_bytes:
        header += struct.pack("B", byte)
    outfile.write(header)

    # write the strings
    for pair in strings:
        string = pair['translated']
        outfile.write(struct.pack("<I", len(string)))
        outfile.write(string.encode("latin-1"))

    outfile.close()
