#!/usr/bin/python

import os
import struct
import sys

HEADER_SIZE = 12

SPANISH_MAP = {
    ord('?'): { 'pos': 128, 'rotate': True },
    ord('!'): { 'pos': 129, 'rotate': True },
    ord('A'): { 'pos': 130, 'rotate': False },
    ord('E'): { 'pos': 131, 'rotate': False },
    ord('I'): { 'pos': 132, 'rotate': False },
    ord('O'): { 'pos': 133, 'rotate': False },
    ord('U'): { 'pos': 134, 'rotate': False },
    ord('U'): { 'pos': 135, 'rotate': False },
    ord('N'): { 'pos': 136, 'rotate': False },
    ord('a'): { 'pos': 137, 'rotate': False },
    ord('e'): { 'pos': 138, 'rotate': False },
    ord('i'): { 'pos': 139, 'rotate': False },
    ord('o'): { 'pos': 140, 'rotate': False },
    ord('u'): { 'pos': 141, 'rotate': False },
    ord('u'): { 'pos': 142, 'rotate': False },
    ord('n'): { 'pos': 143, 'rotate': False }
}

def write_char_pgm(filename, netpbm_header, width, height, pixels, rotate):
    netpbm = open(filename, "wb")
    netpbm.write(netpbm_header)

    if rotate:
        i = len(pixels) - 1
        inc = -1
    else:
        i = 0
        inc = 1
    for y in xrange(height):
        for x in xrange(width):
            netpbm.write("%d " % (pixels[i]))
            i += inc
        netpbm.write("\n")

    netpbm.close()

def unpack_font(font, output_dir):
    # load header
    header = font.read(HEADER_SIZE)
    (char_count, unk1, unk2, global_y, global_x, bits_per_pixel) = struct.unpack("<HHHHHH", header)
    print "%d characters, global (x, y) = (%d, %d), %d bits/pixel" % (char_count, global_x, global_y, bits_per_pixel)

    # load character offset table
    offset_table = []
    offset_bytes = font.read(4 * char_count)
    for i in xrange(char_count):
        offset_table.append(struct.unpack("<I", offset_bytes[i*4:i*4+4])[0])

    # process each character
    payload_start = font.tell()
    payload = font.read()
    for i in xrange(char_count):
        second_file = None
        offset = offset_table[i] - payload_start
        char_header = struct.unpack("<H", payload[offset:offset+2])[0]
        offset += 2
        y_offset = (char_header >> 11) & 0x1F;
        char_height = (char_header >> 5) & 0x3F;
        char_width = char_header & 0x1F;

        byte = struct.unpack("B", payload[offset:offset+1])[0]
        offset += 1
        bits_left = 8
        if bits_per_pixel == 1:
            shifter = 7
            mask = 0x1
        elif bits_per_pixel == 2:
            shifter = 6
            mask = 0x3

        pixels = []
        for y in xrange(char_height):
            for x in xrange(char_width):
                if bits_left == 0:
                    byte = struct.unpack("B", payload[offset:offset+1])[0]
                    offset += 1
                    bits_left = 8
                pixels.append((byte >> shifter) & mask)
                byte <<= bits_per_pixel
                bits_left -= bits_per_pixel

        # write the raw character
        filename = "%s/char-%03d.pgm" % (output_dir, i)
        netpbm_header = "P2\n%d %d\n%d\n" % (char_width, char_height, (1 << bits_per_pixel) - 1)
        write_char_pgm(filename, netpbm_header, char_width, char_height, pixels, False)

        # write the cloned and possibly rotated character
        if i in SPANISH_MAP:
            filename = "%s/char-%03d.pgm" % (output_dir, SPANISH_MAP[i]['pos'])
            write_char_pgm(filename, netpbm_header, char_width, char_height, pixels, SPANISH_MAP[i]['rotate'])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "USAGE: unpack-tsunami-font.py <resource-font-??.dat> <output directory>"
        sys.exit(1)

    # verify parameters
    print "unpacking font '%s' to directory '%s'" % (sys.argv[1], sys.argv[2])
    if not os.path.exists(sys.argv[2]):
        os.makedirs(sys.argv[2])
    font = open(sys.argv[1], "rb")

    unpack_font(font, sys.argv[2])
