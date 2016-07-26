#!/usr/bin/python

# Extract the different data files from the master "Data.dat" file for
# the game "Lost of Missing Island".

import struct
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "USAGE: extract-data-files.py <file.dat>"
        sys.exit(1)

    # open the file
    datfile = open(sys.argv[1], "rb")
    data = datfile.read(4)
    header = struct.unpack("<I", data[0:4])[0]
    print hex(header)

    # skip the offset/size first pair
    data = datfile.read(8)

    # read offset/size pairs until all 0xFs are seen
    count = 1
    files = []
    while 1:
        data = datfile.read(8)
        (offset, size) = struct.unpack("<II", data[0:8])
        if offset == 0xFFFFFFFF and size == 0xFFFFFFFF:
            break
        filename = "file-%03d.dat" % (count)
        print "%s: 0x%X byte @ offset 0x%X" % (filename, size, offset)
        f = { 'filename': filename, 'offset': offset, 'size': size }
        files.append(f)
        count += 1
        
    for f in files:
        # copy the data to new file
        datfile.seek(f['offset'], 0)
        outfile = open(f['filename'], "wb")
        outfile.write(datfile.read(f['size']))
        outfile.close()

