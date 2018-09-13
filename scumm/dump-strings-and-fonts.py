#!/usr/bin/python

# dump-strings-and-fonts.py
#  by Mike Melanson (mike -at- multimedia.cx)
#
# Call the scummtools module to dump the strings and fonts from a resource
# file into a directory structure for modification and translation.

import os
import sys

import scummtools

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "USAGE: dump-strings-and-fonts.py decrypted-resource-file output-directory"
        print "Note: tool will not continue if directory already exists"
        sys.exit(1)

    resourceFile = sys.argv[1]
    outDir = sys.argv[2]

    # parse the tree before creating the output directory since parsing
    # might fail
    data = open(resourceFile, "rb").read()
    resourceTree = scummtools.HETree(None, isRoot=True)
    if not resourceTree.parseBlob(data):
        print "Parsing failed"
        sys.exit(1)

    if os.path.exists(outDir):
        print outDir + " already exists"
        sys.exit(1)

    os.makedirs(outDir)

    stringList = []
    resourceTree.dumpStringsAndFonts(outDir)
