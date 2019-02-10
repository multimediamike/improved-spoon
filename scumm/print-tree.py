#!/usr/bin/python

# print-tree.py
#  by Mike Melanson (mike -at- multimedia.cx)
#
# Call the scummtools module to parse a SCUMM resource file and print
# its hierarchical tree to standard output.

import sys

import scummtools

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "USAGE: print-tree.py scumm-resource-file"
        sys.exit(1)

    scummData = open(sys.argv[1], "rb").read()
    scummTree = scummtools.HETree(None, isRoot=True)
    scummTree.parseBlob(scummData)
    scummTree.printTree()
