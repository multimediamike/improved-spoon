#!/usr/bin/python

# extract-nifpixeldata.py
#  by Mike Melanson (mike -at- multimedia.cx)
#
# This extracts the NifPixelData from a .NIF file and dumps it to
# another image format which can be edited. This only extracts data that
# is RGBA pixel format.
#
# Based partially on this documentation:
#  http://web.archive.org/web/20151110212142/http://niftools.sourceforge.net/doc/nif/index.html

import math
import os.path
import struct
import sys

TOTAL_EXTRA_BYTES = 131
TEXTURE_START_OFFSET = TOTAL_EXTRA_BYTES - 8

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "USAGE: %s <file.NIF>" % (sys.argv[0])
        sys.exit(1)

    filesize = os.path.getsize(sys.argv[1])
    basename = os.path.basename(sys.argv[1])
    pixel_bytes = filesize - TOTAL_EXTRA_BYTES
    if pixel_bytes != 2**int(math.log(pixel_bytes, 2)):
        print "Invalid file size: %d" % (filesize)

    pixel_count = pixel_bytes / 4
    pixel_bits = int(math.log(pixel_count, 2))

    # load the file parts
    f = open(sys.argv[1], "rb")
    header = f.read(TEXTURE_START_OFFSET)
    pixel_data32 = f.read(pixel_bytes)
    f.close()

    # basic checks
    if header[0:32] != "NetImmerse File Format, Version ":
        print "Invalid file signature"
        sys.exit(1)
    if header[0x34:0x3F] != "NiPixelData":
        print "Missing 'NiPixelData' marker"
        sys.exit(1)
    pix_format = struct.unpack("B", header[0x3F])[0]
    if pix_format != 1:
        print "Only supporting pixel format 1 right now (this file is format %d)" % (pix_format)
        sys.exit(1)
    (width, height) = struct.unpack("<II", header[0x6B:0x73])

    # convert the pixels
    pixel_data24 = ""
    for i in range(pixel_count):
        (b, g, r, a) = struct.unpack("BBBB", pixel_data32[i*4:i*4+4])
        pixel_data24 += struct.pack("BBB", r, g, b)

    ppm = "%s.ppm" % (basename)
    print "writing %s" % (ppm)
    f = open(ppm, "wb")
    f.write("P6\n%d %d\n255\n" % (width, height))
    f.write(pixel_data24)
    f.close()

