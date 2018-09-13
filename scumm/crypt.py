#!/usr/bin/python

# crypt.py
#  by Mike Melanson (mike -at- multimedia.cx)
#
# Call the scummtools module to either decrypt or encrypt a SCUMM
# data file.

import sys

import scummtools

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "USAGE: crypt.py input-file output-file key"
        print "Note: the key is in hexadecimal and is usually the value 69"
        sys.exit(1)

    scummtools.crypt(sys.argv[1], sys.argv[2], sys.argv[3])
