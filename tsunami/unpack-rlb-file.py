#!/usr/bin/python

import json
import os
import struct
import sys

import unpack_tsunami_font

BLOCK_HEADER_SIZE = 6
BLOCK_SIGNATURE = "TMI-"
ENTRY_SIZE = 12
RESOURCE_TYPE_STRIP = 1
RESOURCE_TYPE_VISAGE = 4
RESOURCE_TYPE_MESSAGE = 6
RESOURCE_TYPE_FONT = 7
RESOURCE_TYPE_BITMAP = 14
RESOURCE_TYPE_BITMAP_18 = 18
STRIP_STRUCT_SIZE = 126

HANDLED_RESOURCE_TYPES = [ RESOURCE_TYPE_STRIP, RESOURCE_TYPE_VISAGE,
    RESOURCE_TYPE_MESSAGE, RESOURCE_TYPE_FONT, RESOURCE_TYPE_BITMAP_18 ]

def read_cstr(block, offset):
    cstr = ""
    while 1:
        c = block[offset]
        if c == '\0':
            return cstr
        else:
            cstr += c
            offset += 1

def unpack_rle_visage(data, width, height, filename):
    netpbm = open(filename, "w")
    netpbm.write("P2\n%d %d\n255\n" % (width, height))

    # perform RLE decompression
    rle_size = len(data)
    k = 0
    current_width = width
    while k < rle_size:
        byte = struct.unpack("B", data[k])[0]
        k += 1

        if byte & 0x80 == 0:
            # copy byte string
            current_width -= byte
            while byte > 0:
                pixel = struct.unpack("B", data[k])[0]
                k += 1
                netpbm.write("%d " % (pixel))
                byte -= 1
        elif byte & 0x40 == 0:
            # skip bytes (fill with transparent)
            byte &= 0x3F
            current_width -= byte
            while byte > 0:
                netpbm.write("%d " % (transparent))
                byte -= 1
        else:
            # fetch the next byte and expand it
            byte &= 0x3F
            current_width -= byte
            pixel = struct.unpack("B", data[k])[0]
            k += 1
            while byte > 0:
                netpbm.write("%d " % (pixel))
                byte -= 1

        if current_width <= 0:
            netpbm.write("\n")
            current_width = width

    netpbm.close()

def unpack_raw_visage(data, width, height, filename):
    netpbm = open(filename, "w")
    netpbm.write("P2\n%d %d\n255\n" % (width, height))

    # perform RLE decompression
    k = 0
    for y in xrange(height):
        for x in xrange(width):
            pixel = struct.unpack("B", data[k])[0]
            k += 1
            netpbm.write("%d " % (pixel))
        netpbm.write("\n")

    netpbm.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "USAGE: unpack-rlb-file.py </path/to/file.rlb> </path/to/unpack/into>"
        sys.exit(1)

    resource_dir = sys.argv[2]

    # if the output directory already exists, don't go any farther
    if os.path.exists(resource_dir):
        print resource_dir + " already exists"
        sys.exit(1)
    os.makedirs(resource_dir)

    rlb = open(sys.argv[1], "rb")

    # read the main header
    header = rlb.read(BLOCK_HEADER_SIZE)
    if header[0:4] != BLOCK_SIGNATURE:
        print "invalid block signature"
        sys.exit(1)
    (resource_type, entry_count) = struct.unpack("BB", header[4:6])
    entry = rlb.read(ENTRY_SIZE)
    (resource_id, comp_size, uncomp_size, high, res_type, offset) = \
        struct.unpack("<HHHBBI", entry)
    print "index @ 0x%X, %d bytes" % (offset, uncomp_size)

    # load the index
    rlb.seek(offset, 0)
    index = rlb.read(uncomp_size)
    i = 0
    while 1:
        (res_num, block_type, block_offset) = struct.unpack("<HHH", index[i:i+6])
        if res_num == 0xFFFF and block_type == 0xFFFF and block_offset == 0xFFFF:
            #print "end of index"
            break
        offset_high_bits = block_type >> 5
        block_type &= 0x1F
        block_offset = (block_offset | (offset_high_bits << 16)) * 16
        #print "%d: block type %d at 0x%X" % (res_num, block_type, block_offset)

        # check that the block has a valid signature
        rlb.seek(block_offset, 0)
        header = rlb.read(BLOCK_HEADER_SIZE)
        if header[0:4] != BLOCK_SIGNATURE:
            print "  **** block does not have 'TMI-' signature"
            sys.exit(1)

        if block_type in HANDLED_RESOURCE_TYPES:
            print "resource #%d, type %d @ offset 0x%X" % (res_num, block_type, block_offset)
            (resource_type, entry_count) = struct.unpack("BB", header[4:6])
            if resource_type != block_type:
                print "resource type mismatch (index says %d, block says %d)" % (block_type, resource_type)

            # read all of the entries
            entries = []
            for j in xrange(entry_count):
                entry_bytes = rlb.read(ENTRY_SIZE)
                (entry_id, comp_size, uncomp_size, high, res_type, offset) = \
                    struct.unpack("<HHHBBI", entry_bytes)
                print "  id %d, type %d, sizes: (%d, %d, %d), offset = 0x%X" % (entry_id, res_type, comp_size, uncomp_size, high, offset)

                if comp_size != uncomp_size:
                    print "Decompression not implemented yet"
                    sys.exit(1)

                cur_pos = rlb.tell()
                rlb.seek(block_offset + offset, 0)
                payload = rlb.read(uncomp_size)
                entries.append({ 'payload': payload, 'size': uncomp_size })
                rlb.seek(cur_pos, os.SEEK_SET)

            if block_type == RESOURCE_TYPE_FONT:
                filename = "%s/resource-font-%02d.dat" % (resource_dir, res_num)
                print "dumping font %d -> '%s'" % (res_num, filename)
                open(filename, "wb").write(entries[0]['payload'])
                font_dir = "%s/resource-font-%02d" % (resource_dir, res_num)
                if not os.path.exists(font_dir):
                    os.makedirs(font_dir)
                unpack_tsunami_font.unpack_font(open(filename, "rb"), font_dir)
            elif block_type == RESOURCE_TYPE_MESSAGE:
                payload = entries[0]['payload']
                size = entries[0]['size']
                message_list = []
                message = ""
                for j in xrange(size):
                    if payload[j] == '\0':
                        pair = {}
                        pair['English'] = message
                        pair['Spanish'] = message
                        message_list.append(pair)
                        message = ""
                    else:
                        if payload[j] == '\x0D':
                            message += '\n'
                        else:
                            message += payload[j]
    
                message_file = "%s/messages-%04d.json.txt" % (resource_dir, res_num)
                print "dumping message resource %d -> '%s'" % (res_num, message_file)
                open(message_file, "w").write(json.dumps(message_list, indent=2))
            elif block_type == RESOURCE_TYPE_STRIP:
                struct_count = entries[0]['size'] /  STRIP_STRUCT_SIZE
                records = entries[0]['payload']
                messages = entries[1]['payload']
                object_list = []
                for si in range(0, struct_count*STRIP_STRUCT_SIZE, STRIP_STRUCT_SIZE):
                    record = records[si:si+STRIP_STRUCT_SIZE]
                    record_id = struct.unpack("<H", record[12:14])[0]
                    message_list = []
                    for ri in range(44, 44 + (8 * 10), 10):
                        (str_id, offset) = struct.unpack("<HH", record[ri:ri+4])
                        if str_id > 0:
                            message = read_cstr(messages, offset)
                            pair = {}
                            pair['id'] = str_id
                            pair['English'] = message
                            pair['Spanish'] = message
                            message_list.append(pair)
                    speaker_offset = struct.unpack("<H", record[124:126])[0]
                    speaker = read_cstr(messages, speaker_offset)
                    object_list.append({ 'speaker': speaker, 'strings': message_list })

                    strip_file = "%s/strip-%04d.json.txt" % (resource_dir, res_num)
                    print "dumping strip resource %d -> '%s'" % (res_num, strip_file)
                    open(strip_file, "w").write(json.dumps(object_list, indent=2))
            elif block_type == RESOURCE_TYPE_VISAGE and res_num == 4005:
                print "dumping %d visage(s) from resource %d" % (len(entries) - 1, res_num)
                for j in range(1, len(entries)):
                    entry = entries[j]
                    payload = entry['payload']
                    (unk1, unk2, unk3, width, height, center_x, center_y, transparent, flags) = struct.unpack("<HHHHHHHBB", payload[0:16])
                    if width == 0 or height == 0:
                        print "  skipping visage %d-%d (%dx%d)" % (res_num, j, width, height)
                        continue
                    print "  visage %d-%d: %d, %d, %d, (%d, %d), (%d, %d), 0x%02X, 0x%02X" % (res_num, j, unk1, unk2, unk3, width, height, center_x, center_y, transparent, flags)
                    filename = "%s/visage-%d-%d.pgm" % (resource_dir, res_num, j)
                    j += 1
                    rle_compressed = flags & 0x02
                    if rle_compressed:
                        unpack_rle_visage(payload[16:], width, height, filename)
                    else:
                        unpack_raw_visage(payload[16:], width, height, filename)
            elif block_type == RESOURCE_TYPE_BITMAP:
                print "dumping bitmap resource %d" % (res_num)
                filename = "%s/bitmap-%d.pgm" % (resource_dir, res_num)
                (bitmap_width, bitmap_height) = struct.unpack("<HH", entries[0]['payload'][0:4])

                # allocate a bitmap array and plot the tiles into the right spots
                bitmap = [0] * (bitmap_width * bitmap_height)
                j = 1
                BITMAP_TILE_WIDTH = 160
                BITMAP_TILE_HEIGHT = 100
                for tile_x in xrange(bitmap_width / BITMAP_TILE_WIDTH):
                    for tile_y in xrange(bitmap_height / BITMAP_TILE_HEIGHT):
                        print "tile %d: (%d, %d)" % (j, tile_x, tile_y)
                        payload = entries[j]['payload']
                        j += 1
                        src = 0
                        for y in xrange(BITMAP_TILE_HEIGHT):
                            dest = (tile_y * BITMAP_TILE_HEIGHT + y) * bitmap_width + tile_x * BITMAP_TILE_WIDTH
                            for x in xrange(BITMAP_TILE_WIDTH):
                                bitmap[dest] = struct.unpack("B", payload[src])[0]
                                src += 1
                                dest += 1

                # write the bitmap to a PGM file
                pgm = open(filename, "wb")
                pgm.write("P5\n%d %d\n255\n" % (bitmap_width, bitmap_height))
                for pixel in bitmap:
                    pgm.write(struct.pack("B", pixel))
                pgm.close()
            elif block_type == RESOURCE_TYPE_BITMAP_18:
                filename = "%s/bitmap18-%d.pgm" % (resource_dir, res_num)
                print "dumping bitmap (type 18) resource %d -> '%s'" % (res_num, filename)
                pgm = open(filename, "wb")
                pgm.write("P5\n320 200\n255\n")
                pgm.write(entries[0]['payload'])
                pgm.close()

        # advance to next index entry
        i += 6

