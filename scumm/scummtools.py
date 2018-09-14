#!/usr/bin/python

# scummtools.py
#  by Mike Melanson (mike -at- multimedia.cx)
#
# This is a collection of tools for processing data found inside of SCUMM
# engine games.

import json
import os
import re
import struct

stringList = {}
asciiHistogram = {}
for i in range(32, 127):
    asciiHistogram[chr(i)] = 0
asciiHistogram['\t'] = 0

class HEChunk:
    def __init__(self, tag, payload):
        self.tag = tag
        self.payload = payload
        self.payloadSize = len(payload)

class HETree:
    tagChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
    preambleSize = 8
    lscrStringsPattern = re.compile('\x7FT(\d{6,8},\d{4,5})\x7F([^\x00]+)\x00')

    def __init__(self, tag, isRoot=False):
        self.tag = tag
        self.array = []
        self.isRoot = isRoot

    def parseBlob(self, blob):
        # perform a basic sanity check at the root level: make sure that
        # the initial tag is ASCII and the size is less than file size
        if not all(char in self.tagChars for char in blob[0:4]):
            print "First tag of resource is not ASCII"
            return False
        size = struct.unpack(">I", blob[4:8])[0]
        if size > len(blob):
            print "First chunk size is larger than file size (%d > %d)" % (size, len(blob))
            return False

        # proceed with parsing
        self.recurseParseBlob(blob)
        return True

    def recurseParseBlob(self, blob):
        i = 0
        blob_size = len(blob)
        while i < blob_size:
            tag = blob[i:i+4]
            i += 4
            payloadSize = struct.unpack(">I", blob[i:i+4])[0] - self.preambleSize
            i += 4
            # IF the payload is larger than a chunk preamble
            # AND the first 4 bytes of the payload are ASCII
            # AND the next 4 bytes are an int that is smaller than payload size
            # THEN treat the chunk as a container
            nextTag = None
            nextSize = -1
            if payloadSize > self.preambleSize:
                if all(char in self.tagChars for char in blob[i:i+4]):
                    nextTag = blob[i:i+4]
                nextSize = struct.unpack(">I", blob[i+4:i+8])[0]
            if nextTag and nextTag not in ["DIGI", "SDAT"] and (nextSize - self.preambleSize) < payloadSize:
                subtree = HETree(tag)
                subtree.parseBlob(blob[i:i+payloadSize])
                self.array.append(subtree)
            else:
                self.array.append(HEChunk(tag, blob[i:i+payloadSize]))
            i += payloadSize

    # given an open file handle (f), serialize the tree to the file
    def writeTree(self, f):
        sizeOffset = 0
        totalSize = 0
        if not self.isRoot:
            # if this isn't a root container, then write the tree's tag and
            # a placeholder size
            f.write(self.tag)
            sizeOffset = f.tell()
            f.write(struct.pack(">I", 0))
            totalSize += self.preambleSize
        for item in self.array:
            if item.__class__.__name__ == "HEChunk":
                totalSize += self.preambleSize + len(item.payload)
                f.write(item.tag)
                f.write(struct.pack(">I", self.preambleSize + len(item.payload)))
                f.write(item.payload)
            else:
                totalSize += item.writeTree(f)
        if not self.isRoot:
            # if this isn't a root container, then back up and write the
            # actual container size
            currentOffset = f.tell()
            f.seek(sizeOffset, os.SEEK_SET)
            f.write(struct.pack(">I", totalSize))
            f.seek(currentOffset, os.SEEK_SET)
        return totalSize

    def dumpStringsAndFonts(self, outDir):
        stringList = {}
        fontList = []
        self.recurseDumpStringsAndFonts(outDir, stringList, fontList)
        fontCounter = 0
        for font in fontList:
            i = 0
            (size, version) = struct.unpack("<IH", font.payload[i:i+6])
            i += 6
            colorMap = font.payload[i:i+15]
            i += 15
            (bitsPerPixel, fontHeight, numChars) = struct.unpack("<BBH", font.payload[i:i+4])
            print "CHAR", fontCounter, size, version, bitsPerPixel, fontHeight, numChars
            fontCounter += 1
            for n in range(numChars):
                print "  ", n, struct.unpack("<I", font.payload[i:i+4])[0]
                i += 4

    def recurseDumpStringsAndFonts(self, outDir, stringList, fontList):
        for item in self.array:
            if item.__class__.__name__ == "HETree":
                item.recurseDumpStringsAndFonts(outDir, stringList, fontList)
            else:
                if item.tag == "LSCR":
                    payload = item.payload
                    lscrStrings = self.lscrStringsPattern.findall(payload)
                    for (stringId, string) in lscrStrings:
                        if string not in stringList:
                            stringList[string] = [stringId]
                        else:
                            stringList[string].append(stringId)
                        for char in string:
                            asciiHistogram[char] += 1
                elif item.tag == "CHAR":
                    fontList.append(item)

    def printTree(self, depth=0):
        for item in self.array:
            print depth * ' ' + item.tag
            if item.__class__.__name__ == "HETree":
                item.printTree(depth+2)

# Perform a simple byte-wise XOR decryption or encryption, given an input
# filename,  an output filename, and a hexadecimal key in a string, without
# any hex identifier (usually, '69', but not '0x69').
def crypt(inFileName, outFileName, keyStr):
    indata = open(inFileName, "rb").read()
    outfile = open(outFileName, "wb")
    keyByte = int(keyStr, 16)

    print "Processing " + inFileName + " -> " + outFileName + "..."

    # process 8 bytes at a time
    key8x = 0
    deciCounter = len(indata) / 10
    percentage = 0
    for i in range(8):
        key8x = (key8x << 8) | keyByte
    for i in range(len(indata) / 8):
        q_bin = struct.unpack("Q", indata[i*8:i*8+8])[0]
        q_bin ^= key8x
        outfile.write(struct.pack("Q", q_bin))
        deciCounter -= 8
        if (deciCounter < 0):
            percentage += 10
            print str(percentage) + "%..." 
            deciCounter = len(indata) / 10

    # process residual
    base = len(indata) - (len(indata) % 8)
    for i in range(len(indata) % 8):
        b_bin = struct.unpack("B", indata[base+i])[0]
        b_bin ^= keyByte
        outfile.write(struct.pack("B", b_bin))

    print "100%"

    outfile.close()

import sys
if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()

    root = HETree(None, isRoot=True)
    root.parseBlob(data)
    #root.printTree()
    #f = open("newfile", "wb")
    #root.writeTree(f)
    #print json.dumps(stringList, indent=4)
    unusedChars = []
    for char in sorted(asciiHistogram.keys()):
        if asciiHistogram[char] == 0:
            unusedChars.append(char)
    print "Unused characters:"
    print unusedChars
