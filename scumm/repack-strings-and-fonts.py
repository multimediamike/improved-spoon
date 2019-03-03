#!/usr/bin/python

# repack-strings-and-fonts.py
#  by Mike Melanson (mike -at- multimedia.cx)
#
# Call the scummtools module to replace the existing string and font
# resources from one resource file to another resource file. This relies
# on the directory structure created from the script named
# 'dump-strings-and-fonts.py'

import os
import sys

import scummtools

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "USAGE: repack-strings-and-fonts.py decrypted-resource-file new-resource-file string-and-font-directory"
        sys.exit(1)

    oldResourceFile = sys.argv[1]
    newResourceFile = sys.argv[2]
    inDir = sys.argv[3]

    if oldResourceFile == newResourceFile:
        print "new and old resource files can not be the same"
        sys.exit(1)

    # parse the original resource into a tree
    data = open(oldResourceFile, "rb").read()
    resourceTree = scummtools.HETree(None, isRoot=True)
    if not resourceTree.parseBlob(data):
        print "Parsing failed"
        sys.exit(1)

    # replace the string and font resources
    if not resourceTree.repackStringsAndFonts(inDir):
        print "Failed to repack strings and fonts"
        sys.exit(1)

    # write the new resource file
    outFile = open(newResourceFile, "wb")
    resourceTree.writeTree(outFile)
    outFile.close()

