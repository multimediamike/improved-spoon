#!/usr/bin/python

# rebuild-he0-index.py
#  by Mike Melanson (mike -at- multimedia.cx)
#
# Rebuild an HE game's HE0 resource index file. This changes the offsets
# found in the various chunk types.

import struct
import sys

import scummtools

# This function takes a list of chunks which are in the format of:
#  (room number, relative offset, chunk size)
# and serializes them into a new payload of the format:
#  - offset count (LE_16)
#  - list of room numbers (1 byte each)
#  - list of relative offsets (LE_32)
#  - list of chunk sizes
# The exception is the DIRI chunk:
#  - offset count (LE_16)
#  - list of room numbers (1 byte each)
#  - zeroes (LE_32)
#  - list of relative offsets (LE_32)
def generateIndex(chunkList, diriIndex=False):
    roomList = struct.pack("B", 0)
    offsetList = struct.pack("<I", 0)
    sizeList = struct.pack("<I", 0)
    for (roomNumber, offset, chunkSize) in chunkList:
        roomList += struct.pack("B", roomNumber)
        offsetList += struct.pack("<I", offset)
        if diriIndex:
            sizeList += struct.pack("<I", 0)
        else:
            sizeList += struct.pack("<I", chunkSize)

    newPayload = struct.pack("<H", len(chunkList) + 1)
    newPayload += roomList
    if diriIndex:
        newPayload += sizeList
        newPayload += offsetList
    else:
        newPayload += offsetList
        newPayload += sizeList
    
    return newPayload

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "USAGE: rebuild-he0-file.py original-decrypted-he0 new-decrypted-he0 decrypted-he1"
        sys.exit(1)

    origIndexFile = sys.argv[1]
    newIndexFile = sys.argv[2]
    resourceFile = sys.argv[3]

    print "Reading original index (%s)..." % (origIndexFile)
    indexData = open(origIndexFile, "rb").read()
    indexTree = scummtools.HETree(None, isRoot=True)
    indexTree.parseBlob(indexData)

    print "Reading new resource file (%s)..." % (resourceFile)
    resourceData = open(resourceFile, "rb").read()
    resourceTree = scummtools.HETree(None, isRoot=True)
    resourceTree.parseBlob(resourceData)

    # these are the interesting chunk lists: RMIM, RMDA, SCRP, SOUN, AKOS, CHAR, AWIZ
    rmimList = []
    rmdaList = []
    scrpList = []
    sounList = []
    akosList = []
    charList = []
    awizList = []

    # iterate over the LFLF chunks inside the outer LECF chunk; for each LFLF
    # chunk, iterate over the next level of the tree hierarchy and record the
    # relative offsets of the interesting chunks
    lecfTree = resourceTree.array[0]  # skip root layer tree
    if lecfTree.tag != "LECF":
        print "Expected top level chunk of resource tree to be 'LECF' (found '%s')" % (resourceTree.tag)
        sys.exit(1)

    roomNumber = 0
    rmimOffset = None
    for chunk in lecfTree.array:
        if chunk.tag != "LFLF":
            print "Expected 'LFLF' chunk (found '%s')" % (chunk.tag)
            sys.exit(1)
        lflfTree = chunk

        for chunk in lflfTree.array:
            if chunk.tag == "RMIM":
                # increment room number and revise (and record) base offset
                roomNumber += 1
                rmimOffset = chunk.offset
                rmimList.append(rmimOffset)
            elif chunk.tag == "RMDA":
                rmdaList.append((roomNumber, chunk.offset - rmimOffset, chunk.chunkSize))
            elif chunk.tag == "SCRP":
                scrpList.append((roomNumber, chunk.offset - rmimOffset, chunk.chunkSize))
            elif chunk.tag == "SOUN":
                sounList.append((roomNumber, chunk.offset - rmimOffset, chunk.chunkSize))
            elif chunk.tag == "AKOS":
                akosList.append((roomNumber, chunk.offset - rmimOffset, chunk.chunkSize))
            elif chunk.tag == "CHAR":
                charList.append((roomNumber, chunk.offset - rmimOffset, chunk.chunkSize))
            elif chunk.tag == "AWIZ":
                awizList.append((roomNumber, chunk.offset - rmimOffset, chunk.chunkSize))

    # iterate over the index chunks and generate new payloads for relative offsets
    for chunk in indexTree.array:
        if chunk.tag == "DIRI":
            chunk.payload = generateIndex(rmdaList, diriIndex=True)
        elif chunk.tag == "DIRR":
            chunk.payload = generateIndex(rmdaList)
        elif chunk.tag == "DIRS":
            chunk.payload = generateIndex(scrpList)
        elif chunk.tag == "DIRN":
            chunk.payload = generateIndex(sounList)
        elif chunk.tag == "DIRC":
            chunk.payload = generateIndex(akosList)
        elif chunk.tag == "DIRF":
            chunk.payload = generateIndex(charList)
        elif chunk.tag == "DIRM":
            chunk.payload = generateIndex(awizList)
        elif chunk.tag == "DLFL":
            # pack the count (plus 1) and the first (phantom) offset)
            chunk.payload = struct.pack("<HI", len(rmimList) + 1, 0)
            # pack the offset list
            for offset in rmimList:
                chunk.payload += struct.pack("<I", offset)
        elif chunk.tag == "MAXS":
            # update the number of sound records
            newPayload = chunk.payload[0:22]
            newPayload += struct.pack("<H", len(sounList)+1)
            newPayload += chunk.payload[0x18:]
            chunk.payload = newPayload

    # write the new index file
    print "Writing new index file (%s)..." % (newIndexFile)
    outFile = open(newIndexFile, "wb")
    indexTree.writeTree(outFile)
    outFile.close()
