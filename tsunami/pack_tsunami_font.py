#!/usr/bin/python

import os
import struct
import sys

FONT_HEADER_SIZE = 12

def pack_font(font_header_bytes, base_dir):
    # load the sequence of PGM files
    i = 0
    pgm_files = []
    while 1:
        filename = "%s/char-%03d.pgm" % (base_dir, i)
        if not os.path.exists(filename):
            break
        pgm_files.append(open(filename).read())
        i += 1

    # get the bits/pixel from the firstd image
    bits_per_pixel = (int(pgm_files[0].splitlines()[2]) + 1) >> 1

    # adjust the count in the header
    (count32, count16, y_coord, x_coord, bpp) = struct.unpack("<IHHHH", font_header_bytes)
    new_header = struct.pack("<IHHHH", len(pgm_files), len(pgm_files), y_coord, x_coord, bpp)

    # encode each character
    i = 0
    char_offset = FONT_HEADER_SIZE + 4 * len(pgm_files)
    char_list = ""
    for pgm in pgm_files:
        # parse the PGM header
        lines = pgm.splitlines()
        signature = lines[0].strip()
        (width, height) = lines[1].split()
        width = int(width)
        height = int(height)

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

        # record the offset of this character
        new_header += struct.pack("<I", char_offset)
        char_offset += len(encoding)

        # append the new char encoding to the list
        char_list += encoding
        i += 1

    return new_header + char_list

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "USAGE: pack_tsunami_font <original font> <new font> <character directory>"
        sys.exit(1)

    # read the original font header
    font_header_bytes = open(sys.argv[1], "rb").read(FONT_HEADER_SIZE)

    # make sure the directory is there
    if not os.path.exists(sys.argv[3]):
        print "'%s' is not a directory" % (sys.argv[3])
        sys.exit(1)

    # pack the font
    font_data = pack_font(font_header_bytes, sys.argv[3])

    # write the new font
    open(sys.argv[2], "wb").write(font_data)
