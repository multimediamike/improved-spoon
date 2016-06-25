#!/usr/bin/python

import os
import struct
import sys

FONT_HEADER_SIZE = 12

def pack_font(base_name):
    # load the sequence of PGM files
    i = 0
    pgm_files = []
    while 1:
        filename = "%s-char-%03d.pgm" % (base_name, i)
        if not os.path.exists(filename):
            break
        pgm_files.append(open(filename).read())
        i += 1
    print "found %d char files" % (len(pgm_files))

    # get the bits/pixel from the firstd image
    bits_per_pixel = (int(pgm_files[0].splitlines()[2]) + 1) >> 1

    # get the original header
    old_font = open(base_name, "rb")
    header = old_font.read(FONT_HEADER_SIZE)
    old_font.close()

    # adjust the count in the header
    (count32, count16, y_coord, x_coord, bpp) = struct.unpack("<IHHHH", header)
    header = struct.pack("<IHHHH", len(pgm_files), len(pgm_files), y_coord, x_coord, bpp)

    # create a new font file
    new_filename = "new-%s" % (base_name)
    new_font = open(new_filename, "wb")
    new_font.write(header)

    # create a placeholder offset for each character
    new_font.write(struct.pack("<I", 0) * len(pgm_files))

    # encode each character
    i = 0
    for pgm in pgm_files:
        # parse the PGM header
        lines = pgm.splitlines()
        signature = lines[0].strip()
        (width, height) = lines[1].split()
        width = int(width)
        height = int(height)

        # note the current offset, rewind and write it out
        offset = new_font.tell()
        new_font.seek(FONT_HEADER_SIZE + 4 * i, 0)
        new_font.write(struct.pack("<I", offset))
        new_font.seek(offset, 0)

        # create the 2-byte header
        char_header = (height << 5) | (width)
        encoding = struct.pack("<H", char_header)

        # iterate over the lines and encode the pixels
        accumulator = 0
        bit_count = 0
        for y in xrange(height):
            pixels = lines[3+y].split()
            for x in pixels:
                accumulator = (accumulator << bits_per_pixel) | int(x)
                bit_count += bits_per_pixel
                if bit_count == 8:
                    encoding += struct.pack("B", accumulator)
                    accumulator = 0
                    bit_count = 0

        # handle the residual
        if bit_count > 0:
            accumulator <<= (8 - bit_count)
            encoding += struct.pack("B", accumulator)

        new_font.write(encoding)
        i += 1
    new_font.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "USAGE: invoke with base font filename"
        sys.exit(1)

    pack_font(sys.argv[1])
